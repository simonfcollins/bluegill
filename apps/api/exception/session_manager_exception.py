class SessionManagerError(Exception):
    """
    Unified exception for all session + message persistence errors.
    """
    def __init__(self, message: str, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original = original
