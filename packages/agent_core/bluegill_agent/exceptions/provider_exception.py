class ProviderError(Exception):
    pass


class InvalidProviderError(ProviderError):
    pass


class ProviderConnectError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
    pass
