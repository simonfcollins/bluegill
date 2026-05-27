import uuid
from bluegill_shared.models import Session, Message, Role

from api.repository.message_repository import MessageRepository
from api.repository.session_repository import SessionRepository
from api.exception.repository_exception import RepositoryError
from api.exception.session_manager_exception import SessionManagerError


class SessionManager:
    
    def __init__(self, session_repository: SessionRepository, message_repository: MessageRepository) -> None:
        self.session_repository = session_repository
        self.message_repository = message_repository

        
    def new_session(self) -> Session:
        """
        Generate a new session ID and initialize it with the system prompt.
        """
        
        try:
            session_id = str(uuid.uuid4())
            self._add_session(session_id)
            session = self.session_repository.get(session_id)

            if not session:
                raise SessionManagerError(
                    f"Session '{session_id}' was not found after creation"
                )

            return session

        except RepositoryError as e:
            raise SessionManagerError("Failed to create new session") from e

        except Exception as e:
            raise SessionManagerError("Unexpected error in new_session") from e
    
    
    def clear_session(self, session_id: str) -> None:
        """
        Clears the established session user-assistant context while
        retaining skills and bootstrap context.
        """
        
        try:
            self.message_repository.delete_by_session_id(session_id)

        except RepositoryError as e:
            raise SessionManagerError(
                f"Failed to clear session '{session_id}'",
                e
            )

        except Exception as e:
            raise SessionManagerError(
                f"Unexpected error clearing session '{session_id}'",
                e
            )

    
    def load_last_session(self) -> Session:
        """
        Retrieve the last used session. 
        Determined by the most recent message in the SessionManager.
        """
        
        try:
            last_message = self.message_repository.get_last()

            if last_message and last_message.session_id:
                session = self.session_repository.get(last_message.session_id)

                if session:
                    return session

                # last message exists but session doesn't → inconsistent DB state
                raise SessionManagerError(
                    f"Session '{last_message.session_id}' not found for last message"
                )

            # no messages exist → create fresh session
            return self.new_session()

        except RepositoryError as e:
            raise SessionManagerError("Failed to load last session") from e

        except SessionManagerError:
            raise

        except Exception as e:
            raise SessionManagerError("Unexpected error loading last session") from e
    
    
    def get_session(self, session_id: str) -> Session | None:
        """
        Retrieve a session by ID.
        """
        
        try:
            return self.session_repository.get(session_id)

        except RepositoryError as e:
            raise SessionManagerError(
                f"Failed to retrieve session '{session_id}'") from e

        except Exception as e:
            raise SessionManagerError(
                f"Unexpected error retrieving session '{session_id}'") from e
    
    
    def get_sessions(self) -> list[Session]:
        """
        Retrieves all available sessions.
        """
        
        try:
            return self.session_repository.get_all()

        except RepositoryError as e:
            raise SessionManagerError("Failed to retrieve sessions") from e

        except Exception as e:
            raise SessionManagerError("Unexpected error retrieving sessions") from e
        
        
    def update_session(self, session_id: str, name: str | None = None, tokens_used: int | None = None) -> None:
        """
        Rename a session.
        """

        if not name and not tokens_used:
            return

        try:
            session = self.session_repository.get(session_id)

        except RepositoryError as e:
            raise SessionManagerError("Error updating session '{session_id}'") from e
        
        if not session:
            return
        
        updated_session = Session(
            id=session_id,
            name=name if name else session.name,
            tokens_used=tokens_used if tokens_used else session.tokens_used
        )
        
        try:
            self.session_repository.update(updated_session)
            
        except RepositoryError as e:
            raise SessionManagerError(
                f"Failed to update session '{session_id}'") from e

        except Exception as e:
            raise SessionManagerError(
                f"Unexpected error updating session '{session_id}'") from e
      
        
    def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all corresponding messages.
        """
        
        try:
            self.session_repository.delete(session_id)

        except RepositoryError as e:
            raise SessionManagerError(
                f"Failed to delete session '{session_id}'") from e

        except Exception as e:
            raise SessionManagerError(
                f"Unexpected error deleting session '{session_id}'") from e
    
    
    def delete_all_sessions(self) -> None:
        """
        Delete all sessions and messages.
        """
        
        try:
            self.session_repository.delete_all()

        except RepositoryError as e:
            raise SessionManagerError("Failed to delete all sessions") from e

        except Exception as e:
            raise SessionManagerError("Unexpected error deleting all sessions") from e
        
        
    def add_message(self, session_id: str, role: Role, content: str) -> bool:
        """
        Add a Message to SessionManager.
        """
        
        try:
            if self.session_repository.get(session_id):
                self.message_repository.insert(
                    Message(
                        session_id=session_id,
                        role=role,
                        content=content
                    )
                )
                return True
            return False

        except RepositoryError as e:
            raise SessionManagerError(
                f"Failed to add message to session '{session_id}'") from e

        except Exception as e:
            raise SessionManagerError(
                f"Unexpected error adding message to session '{session_id}'") from e

    
    
    def add_messages(self, messages: list[Message]) -> None:
        """
        Add multiple Messages to SessionManager.
        """
        
        try:
            self.message_repository.insert_all(messages)

        except RepositoryError as e:
            raise SessionManagerError("Failed to add messages") from e

        except Exception as e:
            raise SessionManagerError("Unexpected error adding messages") from e


    def get_messages(self, session_id: str) -> list[Message]:
        """
        Get all messages from a given session.
        """
        
        try:
            return self.message_repository.get_by_session_id(session_id)

        except RepositoryError as e:
            raise SessionManagerError(
                f"Failed to get messages for session '{session_id}'") from e

        except Exception as e:
            raise SessionManagerError(
                f"Unexpected error getting messages for session '{session_id}'") from e
        
        
    def _add_session(self, session_id: str, name: str = "New Session", tokens_used: int = 0) -> None:
        """
        Persists a new session entity to the database.
        """
        
        try:
            self.session_repository.insert(
                Session(
                    id=session_id,
                    name=name,
                    tokens_used=tokens_used
                )
            )

        except RepositoryError as e:
            raise SessionManagerError(
                f"Failed to create session '{session_id}'") from e

        except Exception as e:
            raise SessionManagerError(
                f"Unexpected error creating session '{session_id}'") from e
