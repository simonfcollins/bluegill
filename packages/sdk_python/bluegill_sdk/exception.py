class AgentError(Exception):
    def __init__(self, message: str = "") -> None:
        self.message = message
        
class NotFoundError(AgentError):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)
