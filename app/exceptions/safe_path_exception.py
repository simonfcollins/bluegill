class SafePathError(Exception):
    pass

class PathAccessError(SafePathError):
    pass

class PathNotFoundError(SafePathError):
    pass

class IsADirectoryError(SafePathError):
    pass

class IsAFileError(SafePathError):
    pass