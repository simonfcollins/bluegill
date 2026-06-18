from pathlib import Path

import bluegill_agent.exceptions.safe_path_exception as spe

def safe_path(root: Path, path: str) -> Path:
    root = root.resolve()
    candidate = Path(path).resolve() if Path(path).is_absolute() else (root / path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        raise spe.PathAccessError("Access outside workspace is not allowed")

    return candidate
