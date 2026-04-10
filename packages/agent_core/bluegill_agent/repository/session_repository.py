from bluegill_agent.repository.repository import Repository
from bluegill_agent.entity.session import Session
from typing import List

class SessionRepository(Repository[Session, str]):
    
    def __init__(self):
        super().__init__()
        self._init_table()
        
        
    def _init_table(self) -> None:
        """
        Creates the sessions table in the database.
        """
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()
        
    
    def get(self, id: str) -> Session | None:
        """
        Retrieve a session from the database.
        
        Params:
            id - The primary key of the session to be retrieved.
            
        Returns:
            The Session corresponding to the given primary key
            or None if no entity exists with the given key.
        """
        
        cursor = self.conn.execute(
            "SELECT id, name, created_at FROM sessions WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
    
        return Session(
            id=row[0],
            name=row[1],
            created_at=row[2]
        )
        
        
    def get_all(self) -> List[Session]:
        """
        Retrieve all sessions.
        
        Returns:
            A list of Sessions.
        """
        
        cursor = self.conn.execute(
            "SELECT id, name, created_at FROM sessions"
        )
        rows = cursor.fetchall()
        return [Session(
            id=row[0],
            name=row[1],
            created_at=row[2]
            )
            for row in rows
        ]
        
        
    def insert(self, entity: Session) -> None:
        """
        Insert a session into the table.
        
        Params: 
            entity - The Session object to be inserted.
        """
        
        self.conn.execute(
            "INSERT INTO sessions (id, name) VALUES (?, ?)",
            (entity.id, entity.name)
        )
        self.conn.commit()
        
    
    def delete(self, id: str) -> None:
        """
        Delete a session from the table.
        
        Params:
            id - The primary key of the session to delete.
        """
        
        self.conn.execute(
            "DELETE FROM sessions WHERE session_id = ?", (id,)
        )
        self.conn.commit()
        
        
    def delete_all(self) -> None:
        """
        Removes all sessions from the database.
        """
        
        self.conn.execute("DELETE FROM sessions")
        self.conn.commit()


session_repository = SessionRepository()
