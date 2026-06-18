from pathlib import Path

from bluegill_agent.agent.tools.base import Tool
import bluegill_agent.exceptions.safe_path_exception as spe
from bluegill_agent.exceptions.tool_exception import WriteFileError
from bluegill_agent.agent.tools.utils import safe_path

class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file"

    async def run(self, input: dict, working_dir: Path) -> str:
        try:
            path = safe_path(working_dir, input["path"])

            if path.exists() and not path.is_file():
                raise spe.IsADirectoryError(f"{path} is not a file")

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(input["content"])

            return "File written successfully"

        except spe.SafePathError:
            raise
        except Exception as e:
            raise WriteFileError(f"Error using write_file tool: {e}") from e
