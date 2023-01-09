import json
from typing import Any, AnyStr
from deta import Deta 
from config import DETA_PROJECT_KEY

deta = Deta(DETA_PROJECT_KEY)


def upsert_record(db_path: AnyStr, data: Any, key: AnyStr = None):
    db = deta.Base(db_path)
    return db.put(data, key=key)


def read_record(db_path: AnyStr, key: AnyStr, default: Any = {}):
    db = deta.Base(db_path)
    return db.get(key) or default
