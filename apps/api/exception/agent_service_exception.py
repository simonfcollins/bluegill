class AgentServiceError(Exception):
    """
    Base exception class for AgentService.
    """
    
    def __init__(self, message: str, original: Exception | None = None):
        super().__init__(message)
        self.original = original
