import difflib
from pathlib import Path

from bluegill_agent.agent.tools.base import Tool
from bluegill_agent.agent.tools.utils import safe_path
from bluegill_agent.exceptions.tool_exception import EditFileError
import bluegill_agent.exceptions.safe_path_exception as spe


class EditFileTool(Tool):
    name = "edit_file"
    args = (
        "'path': The absolute or relative path to the file, "
        "'content': The full updated contents of the file"
    )
    description = (
        "Replace a file with updated contents. "
        "A unified diff will be generated automatically."
    )

    async def run(self, input: dict, working_dir: Path) -> str:
        try:
            path = safe_path(working_dir, input["path"])

            if path.exists() and not path.is_file():
                raise spe.IsADirectoryError(f"{path} is not a file")

            path.parent.mkdir(parents=True, exist_ok=True)

            original = path.read_text() if path.exists() else ""
            updated = input["content"]

            if updated == original:
                raise EditFileError(
                    "New content is identical to existing file"
                )

            # Generate unified diff for logging/debugging
            diff = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    updated.splitlines(keepends=True),
                    fromfile=f"a/{path.name}",
                    tofile=f"b/{path.name}",
                )
            )

            path.write_text(updated)

            return (
                "File patched successfully\n\n"
                f"Generated diff:\n{diff}"
            )

        except spe.SafePathError:
            raise

        except Exception as e:
            raise EditFileError(
                f"Error using edit_file tool: {e}"
            ) from e
