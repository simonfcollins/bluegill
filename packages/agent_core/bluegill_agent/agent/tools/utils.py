from pathlib import Path

from bluegill_agent.services.workspace_provider import WorkspaceProvider
import bluegill_agent.exceptions.safe_path_exception as spe

BASE_DIR = None


def safe_path(path: str) -> Path:
    global BASE_DIR

    if BASE_DIR is None:
        BASE_DIR = WorkspaceProvider.get_workspace().resolve()

    full_path = (BASE_DIR / path).resolve()

    try:
        full_path.relative_to(BASE_DIR)
    except ValueError:
        raise spe.PathAccessError("Access outside workspace is not allowed")

    return full_path
