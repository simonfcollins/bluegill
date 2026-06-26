import httpx
import json
from typing import AsyncGenerator
from pydantic import ValidationError
from bluegill_shared.models import Message, Session, AgentStreamResponse, StreamRequest, NewSessionRequest
from bluegill_shared.utils import Workspace, Model, Config

from bluegill_sdk.exception import AgentError, NotFoundError


class Agent:
    def __init__(
        self,
        api_url: str = "http://localhost:54345", # URL where the Bluegill API is running.
        provider: str | None = None,             # The model provider (e.g. "ollama")
        model: str | None = None,                # The model to use for queries (e.g. "qwen3-coder:latest")
        session_id: str | None = None,           # The ID of the active session.
        timeout: int = 20,                       # The timeout value injected into the header of all API calls.
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.provider = provider
        self.model = model
        self._session_id = session_id
        self._session_name = ""
        self._workspace_id = ""
        self._tokens_used = 0
        self._messages: list[Message] = []
        self._config = None
        self._timeout = timeout
        self._client = httpx.Client(timeout=self._timeout)
        
        if session_id:
            self.load_session(session_id)


    def new_session(self, workspace_id: str) -> Session:
        """
        Create a new session and set it as the current session.
        Returns the ID of the new session.
        """
        
        try:
            response = self._client.post(
                f"{self.api_url}/sessions",
                json=NewSessionRequest(workspace_id=workspace_id).model_dump()
            )
            response.raise_for_status()
            
            session = Session.model_validate(response.json())
            self._session_id = session.id
            self._session_name = session.name
            self._workspace_id = workspace_id
            self._tokens_used = 0
            self._messages = []
            
            return session
        
        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("Error creating new session") from e
        
    
    def clear_session(self) -> None:
        """
        Clear the context of the active session.
        """
        
        if not self._session_id:
            return

        try:
            response = self._client.post(f"{self.api_url}/sessions/{self.session_id}/clear")
            response.raise_for_status()
            
            self._tokens_used = 0
            self._messages = []
            
        except httpx.HTTPError as e:
            raise AgentError(f"Error clearing session '{self.session_id}'") from e
        
    
    def load_session(self, session_id: str) -> bool:
        """
        Load a session by session ID.
        """
        
        if not session_id: 
            return False
        
        try:
            response = self._client.get(f"{self.api_url}/sessions/{session_id}")
            response.raise_for_status()
            
            session = Session.model_validate(response.json())
            
            if session.id != session_id:
                return False
            
            self._session_id = session_id
            self._session_name = session.name
            self._tokens_used = session.tokens_used
            self._workspace_id = session.workspace_id
            self._load_messages()
            return True
            
        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("Error loading session") from e
        

    def load_last_session(self) -> Session:
        """
        Set the last active session as the active session.
        """
        
        try:
            response = self._client.get(f"{self.api_url}/sessions/last")
            response.raise_for_status()

            session = Session.model_validate(response.json())
            self._session_id = session.id
            self._session_name = session.name
            self._workspace_id = session.workspace_id
            self._tokens_used = session.tokens_used
            self._load_messages()
            
            return session
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError("No sessions found") from e
            
            raise AgentError("Error loading last session") from e

        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("Error loading last session") from e
        
        
    def get_sessions(self) -> list[Session]:
        """
        Retrieve a list of available sessions.
        """
        
        try:
            r = self._client.get(f"{self.api_url}/sessions")
            r.raise_for_status()
            
            return [Session.model_validate(s) for s in r.json()]
        
        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("Error retrieving session list") from e
        
        
    def load_config(self) -> Config:
        """
        Reloads the server config file.
        """
        
        try:
            get_response = self._client.get(f"{self.api_url}/config")
            get_response.raise_for_status()
            
            self._config = Config.model_validate(get_response.json())
            
            return self._config
        
        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("Error retrieving config") from e
            

    def dump(self, session_id: str | None) -> list[Message]:
        """
        Retrieve the entire context of the active session.
        Includes all user, assistant, system, and tooling messages.
        """
        
        if not session_id:
            return []

        try:
            r = self._client.get(
                f"{self.api_url}/sessions/{session_id}/dump",
            )
            r.raise_for_status()
            
            return [Message.model_validate(m) for m in r.json()]

        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("Error retrieving session message dump") from e
    
    
    async def chat_stream(self, prompt: str, think: bool = False) -> AsyncGenerator[AgentStreamResponse, None]:
        """
        Query the Agent. Response is streamed. 
        """
        
        if (
            self.provider is None 
            or self.model is None 
            or self._session_id is None 
            or prompt is None
        ):
            return
        
        payload = StreamRequest(
            provider=self.provider,
            model=self.model,
            session_id=self._session_id,
            prompt=prompt,
            think=think
        )
        
        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream(
                "POST",
                f"{self.api_url}/stream",
                json=payload.model_dump(),
            ) as response:
                
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    await response.aread()
                    detail = response.json().get("detail", str(e))
                    yield AgentStreamResponse(
                        event="error",
                        done=True,
                        content=detail
                    )
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    data = json.loads(line)
                    
                    try:
                        yield AgentStreamResponse.model_validate(data)
                        
                    except ValidationError as e:
                        yield AgentStreamResponse(
                            event="error",
                            content=line
                        )
        
        self.load_session(self._session_id)
        
        
    def service_running(self) -> bool:
        """
        Returns true if the Bluegill agent service is running.
        False otherwise.
        """
        
        try:
            self._client.get(f"{self.api_url}/health")
            return True
            
        except httpx.HTTPError:
            return False
    

    def close(self) -> None:
        """
        Close the http client.
        """
        
        self._client.close()


    # ------------------------
    # Properties
    # ------------------------

    @property
    def session_id(self) -> str | None:
        return self._session_id
    
    
    @session_id.setter
    def session_id(self, session_id: str | None) -> None:
        """
        Setter for self._session_id.
        Sets self._session_id to new value and retrieves the session messages.
        
        Params:
            session_id - The new session_id.
        """
        
        if session_id:
            self.load_session(session_id)
        else:
            self._session_id = None
            self._messages = []
            self._tokens_used = 0
            self._workspace_id = None
            
            
    @property
    def config(self) -> Config:
        return self._config or self.load_config()
    
    
    @property
    def models(self) -> list[Model]:
        return self.config.models
    
    
    @property
    def workspaces(self) -> list[Workspace]:
        return list(self.config.workspaces.values())

    
    @property
    def messages(self) -> list[Message]:       
        return self._messages
    
    
    @property
    def workspace_id(self) -> str | None:
        return self._workspace_id
    
    
    @property
    def tokens_used(self) -> int:
        return self._tokens_used
    
    
    @property
    def timeout(self) -> int:
        return self._timeout
    
    
    @property
    def session_name(self) -> str:
        return self._session_name
    
    
    # ------------------------
    # Internal
    # ------------------------
    
    def _load_messages(self) -> None:
        """
        Load the message chain of the active session.
        Stored by self._messages.
        """
        
        self._messages = self.dump(self.session_id)
        