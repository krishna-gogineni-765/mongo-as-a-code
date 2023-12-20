from typing import List, Dict
from pydantic import BaseModel, SecretStr

class MongoUser(BaseModel):
    username: str
    password: SecretStr
    roles: List[str]

class MongoIndex(BaseModel):
    name: str
    fields: Dict[str, int]
    unique: bool = False

class MongoCollection(BaseModel):
    name: str
    indexes: List[MongoIndex]

class MongoDatabase(BaseModel):
    name: str
    collections: List[MongoCollection]
    users: List[MongoUser]

class MongoCluster(BaseModel):
    name: str
    host: str
    port: int
    username: str
    password: SecretStr
    authentication_database: str
    databases: List[MongoDatabase]
