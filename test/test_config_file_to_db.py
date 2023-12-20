import unittest
from pymongo import MongoClient
from src.mongo_data_model import MongoCluster, MongoDatabase, MongoUser, MongoCollection, MongoIndex
from src.main import main
from pydantic import SecretStr

class TestMongoDBSetup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Mock configuration (replace this with your actual test config)
        cls.cluster = MongoCluster(
            name="test_cluster",
            host="localhost",
            port=27017,
            username="mongolocal",
            password=SecretStr("mongosecret1a"),
            authentication_database="admin",
            databases=[
                MongoDatabase(
                    name="test_db",
                    collections=[
                        MongoCollection(
                            name="test_collection",
                            indexes=[MongoIndex(name="test_index", fields={"field": 1})]
                        )
                    ],
                    users=[MongoUser(username="test_user", password=SecretStr("test_password"), roles=["readWrite"])]
                )
            ]
        )

        main([cls.cluster])

        # Create a client for testing
        cls.client = MongoClient("localhost", 27017, username="mongolocal", password="mongosecret1a", authSource="admin")
        cls.db = cls.client["test_db"]

    @classmethod
    def tearDownClass(cls):
        # Clean up: Drop the test database
        cls.client.drop_database("test_db")
        cls.client.close()

    def test_collection_exists(self):
        collections = self.db.list_collection_names()
        self.assertIn("test_collection", collections)

    def test_index_exists(self):
        indexes = self.db["test_collection"].index_information()
        self.assertIn("test_index", indexes)

    def test_document_insertion(self):
        self.db["test_collection"].insert_one({"field": "value"})
        self.assertEqual(self.db["test_collection"].count_documents({}), 1)

    def test_document_deletion(self):
        self.db["test_collection"].insert_one({"field": "value"})
        self.db["test_collection"].delete_one({"field": "value"})
        self.assertEqual(self.db["test_collection"].count_documents({}), 0)

if __name__ == '__main__':
    unittest.main()
