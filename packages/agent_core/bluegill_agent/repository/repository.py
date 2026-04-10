import sqlite3
from pathlib import Path
from typing import TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar("T")
K = TypeVar("K")

BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "sessions.db"

class Repository(Generic[T, K], ABC):
    
    def __init__(self, db_path: Path=DB_PATH):
        # Create DB connection
        self.conn = sqlite3.connect(db_path, timeout = 5.0, check_same_thread = False)
        # Enable write-ahead logging
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")
    
    
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
    