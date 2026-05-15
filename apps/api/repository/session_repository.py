import sqlite3
from bluegill_shared.models import Session

from api.repository.repository import Repository, with_retry
from api.exception.repository_exception import RepositoryError

class SessionRepository(Repository[Session, str]):
    
    def __init__(self) -> None:
        super().__init__()
        self._init_table()
        
        
    def _init_table(self) -> None:
        """
        Creates the sessions table in the database.
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS sessions (
                            id TEXT PRIMARY KEY,
                            name TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()

            with_retry(op)

        except sqlite3.Error as e:
            raise RepositoryError("Failed to initialize sessions table", e)
        
    
    def get(self, id: str) -> Session | None:
        """
        Retrieve a session from the database.
        """
        
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    "SELECT id, name, created_at FROM sessions WHERE id = ?",
                    (id,)
                )
                row = cursor.fetchone()

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to fetch session '{id}'", e)

        if row is None:
            return None

        return Session(id=row[0], name=row[1], created_at=row[2])
        
        
    def get_all(self) -> list[Session]:
        """
        Retrieve all sessions.
        """
        
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    "SELECT id, name, created_at FROM sessions"
                )
                rows = cursor.fetchall()

        except sqlite3.Error as e:
            raise RepositoryError("Failed to fetch all sessions", e)

        return [
            Session(id=row[0], name=row[1], created_at=row[2])
            for row in rows
        ]
        
        
    def insert(self, entity: Session) -> None:
        """
        Insert a session into the table.
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute(
                        "INSERT INTO sessions (id, name) VALUES (?, ?)",
                        (entity.id, entity.name)
                    )
                    conn.commit()

            with_retry(op)

        except sqlite3.IntegrityError as e:
            raise RepositoryError("Session insert violated constraints", e)

        except sqlite3.Error as e:
            raise RepositoryError("Failed to insert session", e)
        
    
    def delete(self, id: str) -> None:
        """
        Delete a session from the table.
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute(
                        "DELETE FROM sessions WHERE id = ?",
                        (id,)
                    )
                    conn.commit()

            with_retry(op)

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to delete session '{id}'", e)
        
        
    def delete_all(self) -> None:
        """
        Removes all sessions from the database.
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute("DELETE FROM sessions")
                    conn.commit()

            with_retry(op)

        except sqlite3.Error as e:
            raise RepositoryError("Failed to delete all sessions", e)


session_repository = SessionRepository()
