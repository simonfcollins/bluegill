from pathlib import Path

from bluegill_agent.agent.tools.base import Tool
import bluegill_agent.exceptions.safe_path_exception as spe
from bluegill_agent.exceptions.tool_exception import ReadFileError
from bluegill_agent.agent.tools.utils import safe_path


class ReadFileTool(Tool):
    name = "read_file"
    args = "'path': The absolute or relative path to the file to be read"
    description = "Read a file from workspace"

    async def run(self, input: dict, working_dir: Path) -> str:
        try:
            path = safe_path(working_dir, input["path"])

            if not path.exists():
                raise spe.PathNotFoundError(f"{path} does not exist")

            if not path.is_file():
                raise spe.IsADirectoryError(f"{path} is not a file")

            return path.read_text()

        except spe.SafePathError:
            raise
        except Exception as e:
            raise ReadFileError(f"Error using read_file tool: {e}") from e

