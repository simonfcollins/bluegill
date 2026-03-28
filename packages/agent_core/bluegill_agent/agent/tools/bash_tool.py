import asyncio
from bluegill_agent.agent.tools.base import Tool

ALLOWED_COMMANDS = {
    # Directory inspection
    "ls", "tree", "pwd", "find", "du",

    # File inspection
    "cat", "head", "tail", "wc", "stat", "file",

    # Text output / path helpers
    "echo", "dirname", "basename"
}
# TODO : deny commands acting on directories outside of the approved workspace

class BashTool(Tool):
    name = "bash_tool"
    description = "Run safe shell commands (supports multiple commands with && or ;)"

    async def run(self, input: dict) -> str:
        cmd = input.get("command")
        if not cmd:
            return "No command provided"

        # Split by && or ; for sequential execution
        raw_commands = [c.strip() for c in cmd.replace(";", "&&").split("&&") if c.strip()]
        outputs = []

        for single_cmd in raw_commands:
            parts = single_cmd.split()
            if not parts:
                continue
            if parts[0] not in ALLOWED_COMMANDS:
                outputs.append(f"Command not allowed: {parts[0]}")
                continue

            try:
                proc = await asyncio.create_subprocess_exec(
                    *parts,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
                result = (stdout + stderr).decode().strip()
                if result:
                    outputs.append(result)
            except Exception as e:
                outputs.append(f"Error running command '{single_cmd}': {e}")

        return "\n".join(outputs) if outputs else "No output"