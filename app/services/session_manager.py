import sqlite3
from typing import List, Dict
import uuid
from app.agent.bootstrap_prompt import BOOTSTRAP_PROMPT

class PersistentSessionManager:
    def __init__(self, db_path="sessions.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        self.current_session_id = self.load_last_session()

    def _init_db(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def add_message(self, session_id: str, role: str, content: str):
        self.conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        self.conn.commit()

    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        cursor = self.conn.execute(
            """
            SELECT role, content FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit)
        )

        rows = cursor.fetchall()

        # reverse to chronological order
        return [
            {"role": role, "content": content}
            for role, content in reversed(rows)
        ]

    def clear_session(self, session_id: str):
        self.conn.execute(
            "DELETE FROM messages WHERE session_id = ?",
            (session_id,)
        )
        self.conn.commit()
        self.add_message(session_id, "system", BOOTSTRAP_PROMPT)
        
    def new_session(self) -> str:
        """
        Generate a new session ID and initialize it with the system prompt.
        """
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.add_message(session_id, "system", BOOTSTRAP_PROMPT)
        return session_id
    
    def load_last_session(self) -> str:
        cursor = self.conn.execute(
            "SELECT session_id FROM messages ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        return self.new_session()
        
session_manager = PersistentSessionManager()