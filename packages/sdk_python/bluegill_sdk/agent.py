from datetime import UTC, datetime
import httpx

from bluegill_sdk.schemas import (
    GenerateRequest,
    SessionIdRequest,
    Message,
    Session,
)

VALID_PROVIDERS = ["ollama"]


class Agent:
    def __init__(
        self,
        api_url: str = "http://localhost:54345", # URL where the Bluegill API is running.
        provider: str | None = None,          # The model provider (e.g. "ollama")
        model: str | None = None,             # The model to use for queries (e.g. "qwen3-coder:latest")
        session_id: str | None = None,        # The ID of the active session.
        timeout: int = 180,                       # The timeout value injected into the header of all API calls.
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self._provider = None
        self.provider = provider
        self.model = model
        self._session_id = None
        self.session_id = session_id
        self.timeout = timeout
        self._messages: list[Message] = []
        self._client = httpx.Client(timeout=self.timeout)


    # ------------------------
    # Core Methods
    # ------------------------

    def get_sessions(self) -> list[Session]:
        """
        Retrieve a list of available sessions.
        
        Returns:
            A list of sessions.
        """
        
        try:
            r = self._client.get(f"{self.api_url}/sessions")
            r.raise_for_status()
            return [Session(**s) for s in r.json()]
        except httpx.HTTPError:
            return []


    def new_session(self) -> str:
        """
        Creat a new session and set it as the current session.
        
        Returns:
            The ID of the new session.
        """
        
        try:
            r = self._client.post(f"{self.api_url}/new")
            r.raise_for_status()
            self._session_id = r.json().get("session_id")
            self._messages = []
            return self._session_id or ""
        except httpx.HTTPError:
            return ""
        
    
    def clear_session(self) -> None:
        """
        Clear the context of the active session.
        """
        
        if not self._session_id:
            return

        try:
            self._client.post(
                f"{self.api_url}/clear",
                json=SessionIdRequest(
                    session_id=self._session_id
                ).model_dump(),
            )
            self._messages = []
        except httpx.HTTPError:
            pass
        

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

        except httpx.HTTPError:
            pass
        
        
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
                f"{self.api_url}/history",
                params={"session_id": self._session_id},
            )
            r.raise_for_status()
            self._messages = [Message(**m) for m in r.json()]
        except httpx.HTTPError:
            self._messages = []


    def generate(self, prompt: str) -> str:
        """
        Query the model within the active session.
        
        Params:
            prompt: The query to be sent to the model.
            
        Returns:
            The models response to the given query.
        """
        
        if not self.is_ready() or not prompt:
            return ""

        self._messages.append(
            Message(
                role="user",
                content=prompt,
                created_at=datetime.now(UTC).isoformat(),
            )
        )

        payload = GenerateRequest(
            provider=self.provider,
            model=self.model,
            session_id=self._session_id,
            prompt=prompt,
        )

        try:
            r = self._client.post(
                f"{self.api_url}/query",
                json=payload.model_dump(),
            )
            r.raise_for_status()

            result = r.json().get("response", "")

            self._messages.append(
                Message(
                    role="assistant",
                    content=result,
                    created_at=datetime.now(UTC).isoformat(),
                )
            )

            return result

        except httpx.HTTPError:
            return ""


    def dump(self) -> list[Message]:
        """
        Retrieve the entire context of the active session.
        Includes all user, assistant, system, and tooling messages.
        
        Returns:
            A list of messages.
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
        except httpx.HTTPError:
            return []


    def close(self) -> None:
        """
        Close the http client.
        """
        
        self._client.close()


    # ------------------------
    # Helpers
    # ------------------------

    def is_ready(self) -> bool:
        """
        Determines whether or not the Agent is ready to recieve queries.
        
        Returns:
            True if the Agent has been initialized with a provider, model, and active session.
            False otherwise.
        """
        
        return all([self.provider, self.model, self._session_id])


    # ------------------------
    # Properties
    # ------------------------

    @property
    def provider(self) -> str | None:
        return self._provider


    @provider.setter
    def provider(self, provider: str | None) -> None:
        """
        Setter for self._provider.
        Checks that the new provider is a valid model provider.
        
        Params:
            provider - The new provider.
        """
        
        if provider is not None and provider not in VALID_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        self._provider = provider


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
