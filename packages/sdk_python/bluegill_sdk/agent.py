import httpx
import json
from typing import AsyncGenerator
from pydantic import ValidationError
from bluegill_shared.models import *

from bluegill_sdk.exception import AgentError


class Agent:
    def __init__(
        self,
        api_url: str = "http://localhost:54345", # URL where the Bluegill API is running.
        provider: str | None = None,             # The model provider (e.g. "ollama")
        model: str | None = None,                # The model to use for queries (e.g. "qwen3-coder:latest")
        window: int = 8000,                      # The maximum input context window size.
        session_id: str | None = None,           # The ID of the active session.
        timeout: int = 20,                       # The timeout value injected into the header of all API calls.
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.provider = provider
        self.model = model
        self.window = window
        self._session_id = session_id
        self.tokens_used = 0
        self._messages: list[Message] = []
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)
        
        if session_id:
            self.load_session(session_id)


    def new_session(self) -> str:
        """
        Create a new session and set it as the current session.
        Returns the ID of the new session.
        """
        
        try:
            response = self._client.post(f"{self.api_url}/sessions")
            response.raise_for_status()
            
            session = Session.model_validate(response.json())
            self._session_id = session.id
            self.tokens_used = 0
            self._messages = []
            
            return self._session_id or ""
        
        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("error creating new session", e)
        
    
    def clear_session(self) -> None:
        """
        Clear the context of the active session.
        """
        
        if not self._session_id:
            return

        try:
            response = self._client.post(f"{self.api_url}/sessions/{self.session_id}/clear")
            response.raise_for_status()
            
            self.tokens_used = 0
            self._messages = []
            
        except httpx.HTTPError as e:
            raise AgentError(f"error clearing session '{self.session_id}'", e)
        
    
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
            self.tokens_used = session.tokens_used
            self._load_messages()
            return True
            
        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("error loading session", e)
        

    def load_last_session(self) -> None:
        """
        Set the last active session as the active session.
        """
        
        try:
            response = self._client.get(f"{self.api_url}/sessions/last")
            response.raise_for_status()

            session = Session.model_validate(response.json())
            self._session_id = session.id
            self.tokens_used = session.tokens_used
            self._load_messages()

        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("error loading last session", e)
            
        
    def get_sessions(self) -> list[Session]:
        """
        Retrieve a list of available sessions.
        """
        
        try:
            r = self._client.get(f"{self.api_url}/sessions")
            r.raise_for_status()
            
            return [Session.model_validate(s) for s in r.json()]
        
        except (httpx.HTTPError, ValidationError) as e:
            raise AgentError("error retrieving session list", e)


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
            raise AgentError("error retrieving session message dump", e)


    def is_ready(self) -> bool:
        """
        Determines whether or not the Agent is ready to receive queries.
        True if the Agent has been initialized with a provider, model, and active session.
        False otherwise.
        """
        
        return all([self.provider, self.model, self._session_id])
    
    
    async def chat_stream(self, prompt: str) -> AsyncGenerator[AgentStreamResponse, None]:
        """
        Query the Agent. Response is streamed. 
        """
        
        if not self.is_ready() or not prompt:
            return 
        
        payload = StreamRequest(
            provider=self.provider,
            model=self.model,
            window=self.window,
            session_id=self._session_id,
            prompt=prompt
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
        
        self.load_session(self.session_id)
    

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
            self.tokens_used = 0

    
    @property
    def messages(self) -> list[Message]:       
        return self._messages
    
    
    # ------------------------
    # Internal
    # ------------------------
    
    def _load_messages(self) -> None:
        """
        Load the message chain of the active session.
        Stored by self._messages.
        """
        
        self._messages = self.dump(self.session_id)
        