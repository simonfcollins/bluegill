import httpx
import json
from typing import AsyncGenerator
from pydantic import ValidationError
from bluegill_shared.models import *

from bluegill_sdk.exception import AgentError


VALID_PROVIDERS = [None, "ollama"]


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
        self._session_id = None
        self.session_id = session_id
        self.timeout = timeout
        self._messages: list[Message] = []
        self._client = httpx.Client(timeout=self.timeout)


    def new_session(self) -> str:
        """
        Creat a new session and set it as the current session.
        Returns the ID of the new session.
        """
        
        try:
            response = self._client.post(f"{self.api_url}/new")
            response.raise_for_status()
            self._session_id = response.json().get("session_id")
            self._messages = []
            
            return self._session_id or ""
        
        except httpx.HTTPError as e:
            raise AgentError("error creating new session", e)
        
    
    def clear_session(self) -> None:
        """
        Clear the context of the active session.
        """
        
        if not self._session_id:
            return

        try:
            self._client.post(
                f"{self.api_url}/clear",
                params={"session_id": self.session_id}
            )
            self._messages = []
            
        except httpx.HTTPError as e:
            raise AgentError(f"error clearing session '{self.session_id}'", e)
        

    def load_last_session(self) -> None:
        """
        Set the last active session as the active session.
        """
        
        try:
            r = self._client.get(f"{self.api_url}/last")
            r.raise_for_status()

            session = Session(**r.json())
            self._session_id = session.id
            self._load_conversation()

        except httpx.HTTPError as e:
            raise AgentError("error loading last session", e)
            
        
    
    def get_sessions(self) -> list[Session]:
        """
        Retrieve a list of available sessions.
        """
        
        try:
            r = self._client.get(f"{self.api_url}/sessions")
            r.raise_for_status()
            
            return [Session(**s) for s in r.json()]
        
        except httpx.HTTPError as e:
            raise AgentError("error retrieving session list", e)


    def dump(self) -> list[Message]:
        """
        Retrieve the entire context of the active session.
        Includes all user, assistant, system, and tooling messages.
        """
        
        if not self._session_id:
            return []

        try:
            r = self._client.get(
                f"{self.api_url}/dump",
                params={"session_id": self._session_id},
            )
            r.raise_for_status()
            
            return [Message(**m) for m in r.json()]

        except httpx.HTTPError as e:
            raise AgentError("error retrieving session message dump", e)


    def is_ready(self) -> bool:
        """
        Determines whether or not the Agent is ready to recieve queries.
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
        
        self._load_conversation()
    

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
        
        self._session_id = session_id
        self._load_conversation()

    
    @property
    def messages(self) -> list[Session]:       
        return self._messages
    
    
    # ------------------------
    # Internal
    # ------------------------
    
    def _load_conversation(self) -> None:
        """
        Load the user-assistant message chain of the active session.
        Stored by self._messages.
        """
        
        if not self._session_id:
            self._messages = []
            return

        try:
            r = self._client.get(
                f"{self.api_url}/dump",
                params={"session_id": self._session_id},
            )
            r.raise_for_status()
            self._messages = [Message.model_validate(m) for m in r.json()]
            
        except httpx.HTTPError as e:
            raise AgentError("error loading conversation", e)
