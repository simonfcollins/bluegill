class ProviderError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
    


class InvalidProviderError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message)


class AbilityError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message)
