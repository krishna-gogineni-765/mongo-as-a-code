from typing import List

import yaml
from pymongo import MongoClient, errors
from pymongo.database import Database

from src.mongo_data_model import MongoUser, MongoCollection, MongoCluster


def parse_config_file(file_path: str) -> List[MongoCluster]:
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    try:
        clusters = []
        for cluster_config in config['clusters']:
            cluster = MongoCluster(
                name=cluster_config['name'],
                host=cluster_config['host'],
                port=cluster_config['port'],
                username=cluster_config['username'],
                password=SecretStr(cluster_config['password']),
                authentication_database=cluster_config['authentication_database'],
                databases=[
                    MongoDatabase(
                        name=db['name'],
                        users=[
                            MongoUser(username=user['username'], password=SecretStr(user['password']), roles=user['roles'])
                            for user in db.get('users', [])],
                        collections=[
                            MongoCollection(
                                name=col['name'],
                                indexes=[
                                    MongoIndex(name=index['name'],
                                               fields={field: order for d in index['fields'] for field, order in d.items()},
                                               unique=index.get('unique', False))
                                    for index in col.get('indexes', [])
                                ]
                            ) for col in db.get('collections', [])
                        ]
                    ) for db in cluster_config['databases']
                ]
            )
            clusters.append(cluster)
        return clusters
    except KeyError as e:
        raise KeyError(f"Missing key {e} in config file")

def create_users(db: Database, users: List[MongoUser]):
    for user in users:
        try:
            db.command(
                "createUser",
                user.username,
                pwd=user.password.get_secret_value(),
                roles=[{"role": role, "db": db.name} for role in user.roles]
            )
        except errors.OperationFailure as e:
            print(f"Error creating user {user.username}: {e}")

def create_collections(db: Database, collections: List[MongoCollection]):
    for collection in collections:
        coll = db[collection.name]
        for index in collection.indexes:
            try:
                coll.create_index([(field, order) for field, order in index.fields.items()], name=index.name, unique=index.unique)
            except errors.OperationFailure as e:
                print(f"Error creating index {index.name} in collection {collection.name}: {e}")

def setup_cluster(cluster: MongoCluster):
    client = MongoClient(
        host=cluster.host,
        port=cluster.port,
        username=cluster.username,
        password=cluster.password.get_secret_value(),
        authSource=cluster.authentication_database
    )

    for db_config in cluster.databases:
        db = client[db_config.name]
        create_users(db, db_config.users)
        create_collections(db, db_config.collections)

def sync_config_file_to_db(config_file_path):
    clusters = parse_config_file(config_file_path)
    for cluster in clusters:
        setup_cluster(cluster)
