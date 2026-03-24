from pathlib import Path
from app.agent.tools.base import Tool
from app.services.logger import get_logger

BASE_DIR = Path("./").resolve()

def safe_path(path: str) -> Path:
    full_path = (BASE_DIR / path).resolve()
    try:
        full_path.relative_to(BASE_DIR)
    except ValueError:
        raise ValueError("Access outside workspace is not allowed")

    if not full_path.exists():
        raise FileNotFoundError(f"{full_path} does not exist")

    if not full_path.is_file():
        raise IsADirectoryError(f"{full_path} is not a file")
    
    return full_path


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read a file from workspace"

    async def run(self, input: dict) -> str:
        path = safe_path(input["path"])
        return path.read_text()


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file"

    async def run(self, input: dict) -> str:
        path = safe_path(input["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(input["content"])
        return "File written successfully"


class EditFileTool(Tool):
    name = "edit_file"
    description = "Replace text in a file"

    async def run(self, input: dict) -> str:
        path = safe_path(input["path"])
        content = path.read_text()
        updated = content.replace(input["old"], input["new"])
        path.write_text(updated)
        return "File edited successfully"