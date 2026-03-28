from pathlib import Path
from bluegill_agent.agent.tools.base import Tool
import bluegill_agent.exceptions.safe_path_exception as spe
from bluegill_agent.exceptions.tool_exception import *
from bluegill_agent.services.workspace_provider import WorkspaceProvider

BASE_DIR = None

def safe_path(path: str) -> Path:
    global BASE_DIR
    
    if BASE_DIR is None:
        BASE_DIR = WorkspaceProvider.get_workspace()
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
    