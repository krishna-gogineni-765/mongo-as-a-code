from typing import List

from src.mongo_data_model import MongoDatabase, MongoUser, MongoCluster

class IndexDiff:
    def __init__(self):
        self.added = []
        self.removed = []

class CollectionDiff:
    def __init__(self):
        self.added = []
        self.removed = []
        self.changed = {}  # Key is collection name

class RolesDiff:
    def __init__(self):
        self.added = []
        self.removed = []

class UserDiff:
    def __init__(self):
        self.added = []
        self.removed = []
        self.changed = {}  # Key is username

class DatabaseDiff:
    def __init__(self):
        self.added = []
        self.removed = []
        self.changed = {}
        self.users_diff = {}

class ClusterDiff:
    def __init__(self):
        self.databases = DatabaseDiff()

def generate_user_diff(user_list_control: List[MongoUser], user_list_test: List[MongoUser]) -> UserDiff:
    diff = UserDiff()
    user_names_control = set(user.username for user in user_list_control)
    user_names_test = set(user.username for user in user_list_test)
    diff.added = [user for user in user_list_test if user.username not in user_names_control]
    diff.removed = [user for user in user_list_control if user.username not in user_names_test]
    for user in user_list_control:
        if user.username in user_names_test:
            user_test = next(user_test for user_test in user_list_test if user_test.username == user.username)
            roles_diff = RolesDiff()
            roles_diff.added = [role for role in user_test.roles if role not in user.roles]
            roles_diff.removed = [role for role in user.roles if role not in user_test.roles]
            if roles_diff.added or roles_diff.removed:
                diff.changed[user.username] = roles_diff
    return diff

def generate_collection_diff(db1: MongoDatabase, db2: MongoDatabase) -> CollectionDiff:
    collection_diff = CollectionDiff()

    # Compare collections
    coll_names1 = set(coll.name for coll in db1.collections)
    coll_names2 = set(coll.name for coll in db2.collections)
    collection_diff.added = [coll for coll in db2.collections if coll.name not in coll_names1]
    collection_diff.removed = [coll for coll in db1.collections if coll.name not in coll_names2]

    # Compare indexes for matching collection
    for coll1 in db1.collections:
        if coll1.name in coll_names2:
            coll2 = next(coll for coll in db2.collections if coll.name == coll1.name)
            index_diff = IndexDiff()
            index_names1 = set(idx.name for idx in coll1.indexes)
            index_names2 = set(idx.name for idx in coll2.indexes)
            index_diff.added = [idx for idx in coll2.indexes if idx.name not in index_names1]
            index_diff.removed = [idx for idx in coll1.indexes if idx.name not in index_names2]
            if index_diff.added or index_diff.removed:
                collection_diff.changed[coll1.name] = index_diff

    return collection_diff


def generate_cluster_diff(cluster1: MongoCluster, cluster2: MongoCluster) -> ClusterDiff:
    diff = ClusterDiff()

    # Compare databases
    db_names1 = set(db.name for db in cluster1.databases)
    db_names2 = set(db.name for db in cluster2.databases)

    diff.databases.added = [db for db in cluster2.databases if db.name not in db_names1]
    diff.databases.removed = [db for db in cluster1.databases if db.name not in db_names2]

    # Compare collections, indexes, and users within each database
    for db1 in cluster1.databases:
        if db1.name in db_names2:
            db2 = next(db for db in cluster2.databases if db.name == db1.name)
            collection_diff = generate_collection_diff(db1, db2)
            user_diff = generate_user_diff(db1.users, db2.users)
            if collection_diff.added or collection_diff.removed or collection_diff.changed:
                diff.databases.changed[db1.name] = collection_diff
            if user_diff.added or user_diff.removed or user_diff.changed:
                diff.databases.users_diff[db1.name] = user_diff
    return diff