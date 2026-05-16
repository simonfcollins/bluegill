from typing import Callable, Any
from fastapi import HTTPException

from api.exception.session_manager_exception import SessionManagerError


def try_session_manager(fun: Callable[..., Any], **xargs: Any) -> Any:
    """
    Helper function that trys executing the given SessionManager method.
    Raises a FastAPI HTTPException if fun raises an error.
    """
    
    try:
        return fun(**xargs)
    except SessionManagerError as e:
        raise HTTPException(status_code=500, detail=str(e))
