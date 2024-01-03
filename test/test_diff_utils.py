import unittest
from src.diff_utils import generate_cluster_diff, DatabaseDiff, CollectionDiff, IndexDiff, UserDiff, MongoCluster, \
    MongoDatabase, MongoCollection, MongoIndex, MongoUser
from pydantic import SecretStr


# Replace 'your_diff_script' with the actual name of your script

class TestMongoClusterDiff(unittest.TestCase):

    def create_mock_cluster(self, name, num_dbs, num_collections_per_db, num_indexes_per_collection, users_per_db):
        return MongoCluster(
            name=name,
            host="localhost",
            port=27017,
            username="user",
            password=SecretStr("pass"),
            authentication_database="admin",
            databases=[
                MongoDatabase(
                    name=f"db_{i}",
                    collections=[
                        MongoCollection(
                            name=f"collection_{j}",
                            indexes=[MongoIndex(name=f"index_{k}", fields={"field": 1}, unique=False)
                                     for k in range(num_indexes_per_collection)]
                        ) for j in range(num_collections_per_db)
                    ],
                    users=[MongoUser(username=f"user_{l}", password=SecretStr("pass"), roles=["readWrite"])
                           for l in range(users_per_db[i])]
                ) for i in range(num_dbs)
            ]
        )

    def test_no_difference(self):
        cluster1 = self.create_mock_cluster("Cluster1", 2, 2, 2, [2, 2])
        cluster2 = self.create_mock_cluster("Cluster1", 2, 2, 2, [2, 2])

        diff = generate_cluster_diff(cluster1, cluster2)
        self.assertFalse(diff.databases.added)
        self.assertFalse(diff.databases.removed)
        self.assertFalse(diff.databases.changed)
        self.assertFalse(diff.databases.users_diff)

    def test_added_user_in_database(self):
        cluster1 = self.create_mock_cluster("Cluster1", 1, 2, 2, [1])
        cluster2 = self.create_mock_cluster("Cluster1", 1, 2, 2, [2])  # One extra user in the database

        diff = generate_cluster_diff(cluster1, cluster2)
        self.assertTrue(diff.databases.users_diff)
        self.assertEqual(len(diff.databases.users_diff["db_0"].added), 1)
        self.assertEqual(diff.databases.users_diff["db_0"].added[0].username, "user_1")

    def test_removed_user_in_database(self):
        cluster1 = self.create_mock_cluster("Cluster1", 1, 2, 2, [2])
        cluster2 = self.create_mock_cluster("Cluster1", 1, 2, 2, [1])  # One less user in the database

        diff = generate_cluster_diff(cluster1, cluster2)
        self.assertTrue(diff.databases.users_diff)
        self.assertEqual(len(diff.databases.users_diff["db_0"].removed), 1)
        self.assertEqual(diff.databases.users_diff["db_0"].removed[0].username, "user_1")

    # Additional test cases can be added as needed...

if __name__ == '__main__':
    unittest.main()

