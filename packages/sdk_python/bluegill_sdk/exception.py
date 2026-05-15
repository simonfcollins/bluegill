class AgentError(Exception):
    def __init__(self, message: str = "", e: Exception = None) -> None:
        self.message = message
        self.original = e
