import sqlite3
from pathlib import Path
from typing import Any, TypeVar, Generic
from abc import ABC, abstractmethod
import threading
import time

T = TypeVar("T")
K = TypeVar("K")

BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "sessions.db"

WRITE_LOCK = threading.Lock()


def create_connection(db_path: Path) -> sqlite3.Connection:
    """
    Creates and returns a new sqlite3.Connection instance.
    """
    
    conn = sqlite3.connect(
        db_path,
        timeout=5.0,
        check_same_thread=True 
    )
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def with_retry(fn, retries: int = 5) -> Any:
    """
    Retry wrapper for SQLite 'database is locked' errors.
    """
    
    for i in range(retries):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                time.sleep(0.05 * (i + 1))
                continue
            raise
    raise sqlite3.OperationalError("SQLite retry limit exceeded")


class Repository(Generic[T, K], ABC):
    
    def __init__(self, db_path: Path=DB_PATH) -> None:
        self.db_path = db_path
        
    
    def _conn(self) -> sqlite3.Connection:
        return create_connection(self.db_path)
    
    
    @abstractmethod
    def _init_table(self) -> None:
        """
        Abstract method to create the associated database table.
        CREATE TABLE IF NOT EXISTS is recommended.
        """
        pass
    
    
    @abstractmethod
    def get(self, id: K) -> T | None:
        """
        Retrieve an entity from the table given a primary key.
        """
        pass
    
    
    @abstractmethod
    def get_all(self) -> list[T]:
        """
        Retrieve all entities from the table.
        !!! USE WITH CAUTION !!!
        """
        pass
    
    
    @abstractmethod
    def insert(self, entity: T) -> None:
        """
        Insert an entry into the table.
        """
        pass


    @abstractmethod
    def delete(self, id: K) -> None:
        """
        Delete an entry from the table.
        """
        pass
    