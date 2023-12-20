import unittest
from pymongo import MongoClient
from src.cluster_to_data_model import mongo_to_datamodel

class TestMongoConfigLoading(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Establish a connection to the MongoDB server
        cls.client = MongoClient(host="localhost", port=27017, username="mongolocal", password="mongosecret1a", authSource="admin")

        cls.db_name = 'test_db_2'
        cls.db = cls.client[cls.db_name]
        cls.db['test_collection'].insert_one({'key': 'value'})  # Create a collection with a document
        cls.db.command("createUser", "test_user", pwd="password", roles=["readWrite"])

    @classmethod
    def tearDownClass(cls):
        # Clean up: Drop the test database and close connection
        cls.client.drop_database(cls.db_name)
        cls.client.close()

    def test_config_loading(self):
        cluster = mongo_to_datamodel("MyCluster", "localhost", 27017, "mongolocal", "mongosecret1a", "admin")

        self.assertIn(self.db_name, [db.name for db in cluster.databases])
        test_db = next(db for db in cluster.databases if db.name == self.db_name)

        self.assertIn("test_collection", [col.name for col in test_db.collections])
        self.assertIn("test_user", [user.username for user in test_db.users])

if __name__ == '__main__':
    unittest.main()
