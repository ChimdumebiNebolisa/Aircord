from aircord.config import DB_PATH
from aircord.db.repositories import Repository


def get_repository() -> Repository:
    return Repository(DB_PATH)

