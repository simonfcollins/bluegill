import httpx
from bluegill_sdk.schemas import GenerateRequest, SessionIdRequest

VALID_PROVIDERS = ["ollama"]

class Agent:
    """
    Async client for interacting with the Bluegill API.

    Features:
    - Persistent HTTP client (connection pooling)
    - Session management
    - Safe request handling
    """

    def __init__(
        self,
        api_url: str = "http://localhost:54345",
        provider: str | None = None,
        model: str | None = None,
        session_id: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self._provider = None
        self.provider = provider  # go through setter
        self.model = model
        self.session_id = session_id
        self.timeout = timeout

        self._client: httpx.AsyncClient | None = None

    # ------------------------
    # Lifecycle
    # ------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client


    async def close(self) -> None:
        """Close underlying HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


    # ------------------------
    # Core Methods
    # ------------------------

    async def generate_with_model(self, provider: str, model: str, prompt: str) -> str:
        """
        Generate response using explicit provider + model.
        """
        if not prompt:
            return ""

        client = await self._get_client()

        payload = GenerateRequest(
            provider=provider,
            model=model,
            session_id=self.session_id,
            prompt=prompt,
        )

        try:
            response = await client.post(
                f"{self.api_url}/generate",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            return response.json().get("result", "")

        except httpx.HTTPError:
            return ""


    async def generate(self, prompt: str) -> str:
        """
        Generate using configured provider + model.
        """
        if not self.is_ready():
            raise ValueError("Agent not fully configured")

        return await self.generate_with_model(
            self.provider, self.model, prompt
        )


    async def clear_session(self) -> None:
        """
        Clear current session on server.
        """
        if not self.session_id:
            return

        client = await self._get_client()

        payload = SessionIdRequest(session_id=self.session_id)

        try:
            await client.post(
                f"{self.api_url}/clear",
                json=payload.model_dump(),
            )
        except httpx.HTTPError:
            pass


    async def create_session(self) -> str:
        """
        Create new session and store it.
        """
        client = await self._get_client()

        try:
            response = await client.post(f"{self.api_url}/new")
            response.raise_for_status()

            self.session_id = response.json().get("session_id")
            return self.session_id or ""

        except httpx.HTTPError:
            return ""
        
    
    async def get_sessions(self) -> list[str]:
        """
        Get a list of all available sessions.
        """
        client = await self._get_client()
        
        try:
            response = await client.get(f"{self.api_url}/sessions")
            response.raise_for_status()
            
            return response.json().get("sessions", [])
        
        except httpx.HTTPError:
            return []
        
        
    async def get_last_session(self) -> str:
        """
        Get the last active session.
        """
        client = await self._get_client()
        
        try:
            response = await client.get(f"{self.api_url}/last")
            response.raise_for_status()
            
            return response.json()
        
        except httpx.HTTPError:
            return {"session_id": "", "name": ""}
        

    async def dump(self) -> list[dict]:
        """
        Get session message history.
        """
        if not self.session_id:
            return []

        client = await self._get_client()

        try:
            response = await client.get(
                f"{self.api_url}/dump",
                params={"session_id": self.session_id},
            )
            response.raise_for_status()

            return response.json().get("messages", [])

        except httpx.HTTPError:
            return []


    async def compact(self):
        raise NotImplementedError


    # ------------------------
    # Helpers
    # ------------------------

    def is_ready(self) -> bool:
        return all([self.provider, self.model, self.session_id])


    # ------------------------
    # Properties
    # ------------------------

    @property
    def provider(self) -> str | None:
        return self._provider


    @provider.setter
    def provider(self, provider: str | None) -> None:
        if provider is not None and provider not in VALID_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        self._provider = provider
