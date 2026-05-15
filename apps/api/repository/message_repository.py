import sqlite3
from bluegill_shared.models import Message

from api.repository.repository import Repository, with_retry
from api.exception.repository_exception import RepositoryError

class MessageRepository(Repository[Message, int]):
    
    def __init__(self) -> None:
        super().__init__()
        self._init_table()
    
    
    def _init_table(self) -> None:
        """
        Creates the messages table in the database. 
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            session_id TEXT,
                            role TEXT,
                            content TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (session_id)
                                REFERENCES sessions(id)
                                ON DELETE CASCADE
                        )
                    """)
                    conn.commit()

            with_retry(op)

        except sqlite3.Error as e:
            raise RepositoryError("Failed to initialize messages table", e)
        
        
    def get(self, id: int) -> Message | None:
        """
        Retrieve a single message from the database.
        """
        
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, session_id, role, content, created_at
                    FROM messages
                    WHERE id = ?
                    """,
                    (id,)
                )
                row = cursor.fetchone()
                
        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to fetch message '{id}'", e)

        if row is None:
            return None

        return Message(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            created_at=row[4]
        )
    
    
    def get_all(self) -> list[Message]:
        """
        Retrieve all messages.
        """
        
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, session_id, role, content, created_at
                    FROM messages
                    """
                )
                rows = cursor.fetchall()

        except sqlite3.Error as e:
            raise RepositoryError("Failed to fetch all messages", e)

        return [
            Message(id=row[0], session_id=row[1], role=row[2], content=row[3], created_at=row[4])
            for row in rows
        ]
        
        
    def get_by_session_id(self, session_id: str) -> list[Message]:
        """
        Retrieve all messages from the given session.
        """
        
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, session_id, role, content, created_at
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY id ASC
                    """,
                    (session_id,)
                )
                rows = cursor.fetchall()

        except sqlite3.Error as e:
            raise RepositoryError(
                f"Failed to fetch messages for session '{session_id}'", e)

        return [
            Message(
                id=row[0], 
                session_id=row[1], 
                role=row[2], 
                content=row[3], 
                created_at=row[4]
            )
            for row in rows
        ]
        
    
    def get_last(self) -> Message | None:
        """
        Retrieve the most recent message.
        """
        
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, session_id, role, content, created_at
                    FROM messages
                    ORDER BY id DESC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()

        except sqlite3.Error as e:
            raise RepositoryError("Failed to fetch last message", e)

        if row is None:
            return None

        return Message(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            created_at=row[4]
        )
   
    
    def insert(self, entity: Message) -> None:
        """
        Insert a message into the table.
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute(
                        """
                        INSERT INTO messages (session_id, role, content)
                        VALUES (?, ?, ?)
                        """,
                        (entity.session_id, entity.role, entity.content)
                    )
                    conn.commit()

            with_retry(op)

        except sqlite3.IntegrityError as e:
            raise RepositoryError("Message insert violated constraints", e)

        except sqlite3.Error as e:
            raise RepositoryError("Failed to insert message", e)
        
        
    def insert_all(self, entities: list[Message]) -> None:
        """
        Bulk insert multiple messages into the table.
        """

        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.executemany(
                        """
                        INSERT INTO messages (session_id, role, content)
                        VALUES (?, ?, ?)
                        """,
                        [(e.session_id, e.role, e.content) for e in entities]
                    )
                    conn.commit()

            with_retry(op)

        except sqlite3.Error as e:
            raise RepositoryError("Failed to bulk insert messages", e)
        
    
    def delete(self, id: int) -> None:
        """
        Delete a message from the table.
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute(
                        "DELETE FROM messages WHERE id = ?",
                        (id,)
                    )
                    conn.commit()

            with_retry(op)

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to delete message '{id}'", e)
    
    
    def delete_by_session_id(self, session_id: str) -> None:
        """
        Delete all messages corresponding to the given session_id.
        """
        
        try:
            def op() -> None:
                with self._conn() as conn:
                    conn.execute(
                        "DELETE FROM messages WHERE session_id = ?",
                        (session_id,)
                    )
                    conn.commit()

            with_retry(op)

        except sqlite3.Error as e:
            raise RepositoryError(
                f"Failed to delete messages for session '{session_id}'", e)
    
message_repository = MessageRepository()
