class RepositoryError(Exception):
    """
    Base exception for all repository/database errors.
    """
    
    def __init__(self, message: str, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original = original
