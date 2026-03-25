# app/agent/tools/shell_tool.py

import asyncio
from app.agent.tools.base import Tool

ALLOWED_COMMANDS = {
    "ls", "tree", "cat", "echo", "pwd", "head", "tail", "git"
}

class BashTool(Tool):
    name = "bash_tool"
    description = "Run safe shell commands"

    async def run(self, input: dict) -> str:
        cmd = input.get("command")
        if not cmd:
            return "No command provided"

        parts = cmd.split()
        if parts[0] not in ALLOWED_COMMANDS:
            return "Command not allowed"

        try:
            # Async subprocess, capture output
            proc = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)

            # Return output as string
            return (stdout + stderr).decode().strip()
        except Exception as e:
            return f"Error: {e}"