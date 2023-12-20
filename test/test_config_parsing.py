import os
import unittest
from src.mongo_data_model import MongoCluster, MongoDatabase, MongoUser, MongoCollection, MongoIndex
from src.utils import parse_config_file

class TestConfigParsing(unittest.TestCase):
    def tearDown(self):
        if os.path.exists('mock_config.yml'):
            os.remove('mock_config.yml')

    def test_successful_parse(self):
        mock_yaml = """
        clusters:
          - name: test_cluster
            host: localhost
            port: 27017
            username: admin_user
            password: placeholder
            authentication_database: admin
            databases:
              - name: test_db
                users:
                  - username: db_user
                    password: placeholder
                    roles:
                      - readWrite
                      - dbOwner
                  - username: db_user2
                    password: placeholder
                    roles:
                    - readWrite
                collections:
                  - name: test_collection
                    indexes:
                      - name: document_id
                        fields:
                          - id: 1
                        unique: true
        """
        with open('mock_config.yml', 'w') as f:
            f.write(mock_yaml)

        clusters = parse_config_file('mock_config.yml')
        self.assertIsInstance(clusters, list)
        self.assertIsInstance(clusters[0], MongoCluster)
        self.assertEqual(clusters[0].name, "test_cluster")

        # Assertions for cluster level details
        cluster = clusters[0]
        self.assertEqual(cluster.host, 'localhost')
        self.assertEqual(cluster.port, 27017)
        self.assertEqual(cluster.username, 'admin_user')
        self.assertEqual(cluster.password.get_secret_value(), 'placeholder')
        self.assertEqual(cluster.authentication_database, 'admin')

        # Assertions for database level details
        self.assertIsInstance(cluster.databases, list)
        self.assertEqual(len(cluster.databases), 1)
        database = cluster.databases[0]
        self.assertIsInstance(database, MongoDatabase)
        self.assertEqual(database.name, 'test_db')

        # Assertions for user level details
        self.assertIsInstance(database.users, list)
        self.assertEqual(len(database.users), 2)
        user1 = database.users[0]
        self.assertIsInstance(user1, MongoUser)
        self.assertEqual(user1.username, 'db_user')
        self.assertEqual(user1.password.get_secret_value(), 'placeholder')
        self.assertListEqual(user1.roles, ['readWrite', 'dbOwner'])

        # Assertions for collection level details
        self.assertIsInstance(database.collections, list)
        self.assertEqual(len(database.collections), 1)
        collection = database.collections[0]
        self.assertIsInstance(collection, MongoCollection)
        self.assertEqual(collection.name, 'test_collection')

        # Assertions for index level details
        self.assertIsInstance(collection.indexes, list)
        self.assertEqual(len(collection.indexes), 1)
        index = collection.indexes[0]
        self.assertIsInstance(index, MongoIndex)
        self.assertEqual(index.name, 'document_id')
        self.assertDictEqual(index.fields, {'id': 1})
        self.assertTrue(index.unique)

    def test_validation_error(self):
        # Incorrect YAML structure
        bad_yaml = """
        clusters:
          - name: 123  # Name should be a string
        """
        with open('mock_config.yml', 'w') as f:
            f.write(bad_yaml)

        with self.assertRaises(KeyError):
            parse_config_file('mock_config.yml')

if __name__ == '__main__':
    unittest.main()
