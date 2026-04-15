from bluegill_agent.repository.repository import Repository
from bluegill_agent.entity.message import Message

class MessageRepository(Repository[Message, int]):
    
    def __init__(self):
        super().__init__()
        self._init_table()
    
    
    def _init_table(self) -> None:
        """
        Creates the messages table in the database. 
        """
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()
        
        
    def get(self, id: int) -> Message | None:
        """
        Retrieve a single message from the database.
        
        Params:
            id - The primary key of the message to be retrieved.
            
        Returns:
            The Message corresponding to the given primary key
            or None if no entity exists with the given key.
        """
        
        cursor = self.conn.execute(
            "SELECT id, session_id, role, content, created_at FROM messages WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        
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
        
        Returns:
            A list of Messages.
        """
        
        cursor = self.conn.execute(
            "SELECT id, session_id, role, content, created_at FROM messages"
        )
        rows = cursor.fetchall()
        return [Message(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            created_at=row[4]
            )
            for row in rows
        ]
        
        
    def get_by_session_id(self, session_id: str, limit: int = 50) -> list[Message]:
        """
        Retrieve all messages from the given session.
        
        Params:
            session_id - The id of the session from which messages should be retrieved.
            limit - The maximum number of messages to be retrieved from the query.
            
        Returns:
            A list of Messages.
        """
        
        cursor = self.conn.execute(
            """
            SELECT id, session_id, role, content, created_at FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (session_id, limit)
        )
        rows = cursor.fetchall()
        return [Message(
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

        Returns:
            A Message.
        """
        
        cursor = self.conn.execute(
            """
            SELECT id, session_id, role, content, created_at 
            FROM messages 
            ORDER BY created_at DESC 
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        
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
        
        Params:
            entity - The Message object to be inserted.
        """
        
        self.conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (entity.session_id, entity.role, entity.content)
        )
        self.conn.commit()
        
    
    def delete(self, id: int) -> None:
        """
        Delete a message from the table.
        
        Params:
            id - The primary key of the message to delete.
        """
        
        self.conn.execute(
            "DELETE FROM messages WHERE id = ?", (id,)
        )
        self.conn.commit()
    
    
    def delete_by_session_id(self, session_id: str) -> None:
        """
        Delete all messages corresponding to the given session_id.
        
        Params:
            session_id - Identifier of the session for which all associated 
                         messages will be deleted.
        """
        
        self.conn.execute(
            "DELETE FROM messages WHERE session_id = ?",
            (session_id,)
        )
        self.conn.commit()
         
    
message_repository = MessageRepository()
