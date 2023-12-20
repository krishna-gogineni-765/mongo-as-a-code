from typing import List

from pymongo import MongoClient, errors
from pymongo.database import Database

from src.mongo_data_model import MongoUser, MongoCollection, MongoCluster
from src.utils import parse_config_file


# Include your data model classes here...

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

def main(clusters: List[MongoCluster]):
    for cluster in clusters:
        setup_cluster(cluster)

def sync_config_file_to_db(config_file_path):
    clusters = parse_config_file(config_file_path)
    for cluster in clusters:
        setup_cluster(cluster)

if __name__ == "__main__":
    sync_config_file_to_db("/Users/krishna/Desktop/Projects/mongo-as-a-code/test/test_config/simple_local_db.yml")
