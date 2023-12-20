import yaml
from pydantic import SecretStr
from typing import List, Dict

from src.mongo_data_model import MongoCluster, MongoDatabase, MongoUser, MongoCollection, MongoIndex


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