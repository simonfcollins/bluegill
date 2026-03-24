# app/agent/tool_registry.py

from app.agent.tools.file_tools import ReadFileTool, WriteFileTool, EditFileTool
from app.agent.tools.bash_tool import BashTool

TOOLS = {
    "read_file": ReadFileTool(),
    "write_file": WriteFileTool(),
    "edit_file": EditFileTool(),
    "run_bash": BashTool(),
}