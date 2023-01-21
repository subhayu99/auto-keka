import os
import tinydb
from deta import Deta 
from tinydb.queries import where
from tinydb.storages import JSONStorage, MemoryStorage


class DetaDB():
    def __init__(self):
        DETA_PROJECT_KEY = os.environ.get("DETA_PROJECT_KEY", "c0wq9nq6_eEXMEkVAKQbHfmodX6rAUK7gqLBNAvw1")
        self.db = Deta(DETA_PROJECT_KEY)
    
    def upsert_record(self, db_path: str, data: dict, key: str = None):
        return self.db.Base(db_path).put(data, key=key)

    def read_record(self, db_path: str, key: str, default: dict = {}):
        return self.db.Base(db_path).get(key) or default


class TinyDB():
    def __init__(self, in_memory: bool = False):
        if in_memory:
            self.db = tinydb.TinyDB(storage=MemoryStorage)
        else:
            self.db = tinydb.TinyDB("data.json", storage=JSONStorage)
    
    def upsert_record(self, db_path: str, data: dict, key: str = None):
        return self.db.table(db_path).upsert(data | {"key": key}, where("key") == key)
        
    def read_record(self, db_path: str, key: str, default: dict = {}):
        return self.db.table(db_path).get(where("key") == key) or default


def get_db(local: bool = False, in_memory: bool = False):
    return TinyDB(in_memory=in_memory) if local else DetaDB()
