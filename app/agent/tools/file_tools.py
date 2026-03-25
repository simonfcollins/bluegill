from pathlib import Path
from app.agent.tools.base import Tool
import app.exceptions.safe_path_exception as spe
from app.exceptions.tool_exception import *

BASE_DIR = Path("./").resolve()

def safe_path(path: str) -> Path:
    full_path = (BASE_DIR / path).resolve()
    try:
        full_path.relative_to(BASE_DIR)
    except ValueError:
        raise spe.PathAccessError("Access outside workspace is not allowed")

    if not full_path.exists():
        raise spe.PathNotFoundError(f"{full_path} does not exist")

    if not full_path.is_file():
        raise spe.IsADirectoryError(f"{full_path} is not a file")
    
    return full_path


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read a file from workspace"

    async def run(self, input: dict) -> str:
        try:
            path = safe_path(input["path"])
            return path.read_text()
        except spe.SafePathError:
            raise
        except Exception as e:
            raise ReadFileError(f"Error using read_file tool: {e}") from e


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file"

    async def run(self, input: dict) -> str:
        try:
            path = safe_path(input["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(input["content"])
            return "File written successfully"
        except spe.SafePathError:
            raise
        except Exception as e:
            raise WriteFileError(f"Error using write_file tool: {e}") from e


class EditFileTool(Tool):
    name = "edit_file"
    description = "Replace text in a file"

    async def run(self, input: dict) -> str:
        try:
            path = safe_path(input["path"])
            content = path.read_text()
            updated = content.replace(input["old"], input["new"])
            path.write_text(updated)
            return "File edited successfully"
        except spe.SafePathError:
            raise
        except Exception as e:
            raise EditFileError(f"Error using edit_file tool: {e}") from e
    