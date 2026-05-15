from bluegill_agent.agent.tools.read_file import ReadFileTool
from bluegill_agent.agent.tools.write_file import WriteFileTool
from bluegill_agent.agent.tools.edit_file import EditFileTool
from bluegill_agent.agent.tools.bash_tool import BashTool

TOOLS = {
    "read_file": ReadFileTool(),
    "write_file": WriteFileTool(),
    "edit_file": EditFileTool(),
    "run_bash": BashTool(),
}
