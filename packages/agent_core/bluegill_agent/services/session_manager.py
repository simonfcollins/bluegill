import uuid
from bluegill_agent.agent.bootstrap_prompt import BOOTSTRAP_PROMPT
from bluegill_agent.repository.message_repository import message_repository
from bluegill_agent.repository.session_repository import session_repository
from bluegill_agent.entity.message import Message
from bluegill_agent.entity.session import Session


class PersistentSessionManager:
    
    def __init__(self):
        pass


    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Persist a new message entity to the database.
        
        Params:
            session_id - The primary key of the session this new message belongs to.
            role - The entity that generated the message ("user", "assistant", "system", "tool").
            content - The content of the message.
        """
        
        message_repository.insert(Message(
            session_id=session_id,
            role=role,
            content=content
        ))


    def get_messages(self, session_id: str) -> list[Message]:
        """
        Get all messages from a given session.
        
        Params:
            session_id - The id of the session from which messages should be retrieved.
            
        Returns:
            A list of Messages.
        """
        
        return message_repository.get_by_session_id(session_id)


    def _add_session(self, session_id: str, name: str = "New Session") -> None:
        """
        Persists a new session entity to the database.
        
        Params:
            session_id - The primary key of the new session.
            name - A descriptive name for the new session.
        """
        
        session_repository.insert(Session(
            id=session_id, 
            name=name
            )
        )


    def clear_session(self, session_id: str) -> None:
        """
        Clears the established session user-assistant context while
        retaining skills and bootstrap context.
        
        Params:
            session_id - The id of the session to clear.
        """
        
        message_repository.delete_by_session_id(session_id)
        self.add_message(session_id, "system", BOOTSTRAP_PROMPT)
        
        
    def new_session(self) -> Session:
        """
        Generate a new session ID and initialize it with the system prompt.
        
        Returns:
            A new Session.
        """
        
        session_id = str(uuid.uuid4())
        self._add_session(session_id)
        self.add_message(session_id, "system", BOOTSTRAP_PROMPT)
        return session_repository.get(session_id)
    
    
    def load_last_session(self) -> Session:
        """
        Retrieve the last used session.
        
        Returns:
            The last used session or None if no sessions exist.
        """
        
        last_message = message_repository.get_last()
        
        if last_message:
            return session_repository.get(last_message.session_id)
        return self.new_session()
    
    
    def get_sessions(self) -> list[Session]:
        """
        Retrieves all available sessions.
        
        Returns:
            A list of Sessions. 
        """
        
        return session_repository.get_all()
      
        
    def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all corresponding messages.
        
        Params:
            session_id - The id of the session to delete.
        """
        
        session_repository.delete(session_id)
    
    
    def delete_all_sessions(self) -> None:
        """
        Delete all sessions and messages.
        """
        
        session_repository.delete_all()
        
        
session_manager = PersistentSessionManager()
