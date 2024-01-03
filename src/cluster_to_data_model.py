import yaml
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import List, Dict
from pydantic import BaseModel, SecretStr

from src.mongo_data_model import MongoIndex, MongoCollection, MongoUser, MongoCluster, MongoDatabase

def datamodel_to_config(clusters: List[MongoCluster]):
    config = {'clusters': []}
    for cluster in clusters:
        cluster_config = {
            'name': cluster.name,
            'host': cluster.host,
            'port': cluster.port,
            'username': cluster.username,
            'password': cluster.password.get_secret_value(),
            'authentication_database': cluster.authentication_database,
            'databases': []
        }
        for db in cluster.databases:
            db_config = {
                'name': db.name,
                'users': [],
                'collections': []
            }
            for user in db.users:
                db_config['users'].append({
                    'username': user.username,
                    'password': user.password.get_secret_value(),
                    'roles': user.roles
                })
            for collection in db.collections:
                collection_config = {
                    'name': collection.name,
                    'indexes': [],
                }
                for index in collection.indexes:
                    collection_config['indexes'].append({
                        'name': index.name,
                        'fields': [{field: order} for field, order in index.fields.items()],
                        'unique': index.unique
                    })
                db_config['collections'].append(collection_config)
            cluster_config['databases'].append(db_config)
        config['clusters'].append(cluster_config)
    return config

def config_json_to_yml_file(config_json: Dict, file_path: str):
    with open(file_path, 'w') as file:
        yaml.dump(config_json, file)

def get_mongo_indexes(collection: Collection) -> List[MongoIndex]:
    indexes = []
    for index in collection.list_indexes():
        # Skip the default '_id_' index
        if index['name'] != '_id_':
            indexes.append(MongoIndex(
                name=index['name'],
                fields={field: order for field, order in index['key'].items()},
                unique=index.get('unique', False)
            ))
    return indexes


def get_mongo_collections(db) -> List[MongoCollection]:
    collections = []
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        collections.append(MongoCollection(
            name=collection_name,
            indexes=get_mongo_indexes(collection)
        ))
    return collections


def get_mongo_users(db) -> List[MongoUser]:
    users = []
    for user in db.command("usersInfo")['users']:
        roles = [role['role'] for role in user['roles']]
        users.append(MongoUser(
            username=user['user'],
            password=SecretStr(''),  # Passwords are not retrievable
            roles=roles
        ))
    return users


def mongo_to_datamodel(cluster_name, host, port, username, password, auth_db) -> MongoCluster:
    client = MongoClient(host=host, port=port, username=username, password=password, authSource=auth_db)

    databases = []
    for db_name in client.list_database_names():
        print(db_name)
        # Skip system databases
        if db_name not in ["admin", "local", "config"]:
            db = client[db_name]
            databases.append(MongoDatabase(
                name=db_name,
                collections=get_mongo_collections(db),
                users=get_mongo_users(db)
            ))

    return MongoCluster(
        name=cluster_name,
        host=host,
        port=port,
        username=username,
        password=SecretStr(password),
        authentication_database=auth_db,
        databases=databases
    )


if __name__ == "__main__":
    cluster = mongo_to_datamodel("MyCluster", "localhost", 27017, "mongolocal", "mongosecret1a", "admin")
    print(datamodel_to_config([cluster]))