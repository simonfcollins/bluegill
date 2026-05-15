import asyncio
import shlex
import re
from bluegill_agent.agent.tools.base import Tool


# Matches patterns at the beginning of a command segment.
DANGEROUS_PATTERNS = [
    r"^\s*cd\b",
    r"^\s*rm\b",
    r"^\s*mv\b",
    r"^\s*cp\b",
    r"^\s*chmod\b",
    r"^\s*chown\b",
    r"^\s*chgrp\b",
    r"^\s*sudo\b",
    r"^\s*su\b",
    r"^\s*mount\b",
    r"^\s*umount\b",
    r"^\s*shutdown\b",
    r"^\s*reboot\b",
    r"^\s*kill(all)?\b",
    r"^\s*dd\b.*\bof=/dev/\w+",
]

NETWORK_PATTERNS = [
    r"^\s*curl\b",
    r"^\s*wget\b",
    r"^\s*nc\b",
    r"^\s*netcat\b",
    r"^\s*scp\b",
]

COMMAND_SUBSTITUTION_PATTERNS = [
    r"`[^`]+`",
    r"\$\([^)]+\)",
]


class BashTool(Tool):
    name = "bash_tool"
    args = "'command': The command to execute."
    description = "Run shell commands (supports pipes, &&, ;) within a restricted safe subset"

    async def run(self, input: dict) -> str:
        """
        Executes the given bash command in an asyncio subprocess.
        
        Args:
            input: A Python dictionary with the following mappings:
                {"command": "command_str"} where "command_str" is the command to be executed. 
        
        Returns:
            The result of running the bash command.
        """
        cmd = input.get("command")
        if not cmd:
            return "No command provided"

        commands = self._split_commands(cmd)
        outputs = []

        for single_cmd in commands:
            if not self._is_safe(single_cmd):
                outputs.append(f"Blocked command: {single_cmd}")
                continue

            try:
                proc = await asyncio.create_subprocess_shell(
                    single_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

                result = (stdout + stderr).decode(errors="ignore").strip()

                if result:
                    outputs.append(result)

            except asyncio.TimeoutError:
                outputs.append(f"Timeout: {single_cmd}")
            except Exception as e:
                outputs.append(f"Error running '{single_cmd}': {e}")

        return "\n".join(outputs) if outputs else "No output"


    def _split_commands(self, cmd: str) -> list[str]:
        """
        Splits compound commands into segments.
        
        Split on ';' and '&&' while preserving execution order.
        Pipelines are preserved as single units.
        
        Params:
            cmd - The command to segment.
            
        Returns: 
            A list of command segments.
        """
        parts = []
        for segment in cmd.split(";"):
            parts.extend(segment.split("&&"))
        return [p.strip() for p in parts if p.strip()]


    def _is_safe(self, cmd: str) -> bool:
        """
        Checks if the given command is arbitrarily safe to execute.
        
        Safety rules:
        - Validate each pipeline stage independently
        - Block destructive/system/network commands only at command position
        - Allow pipes, &&, ; composition
        
        Params:
            cmd - The command to evaluate.
            
        Returns: 
            True of the command is safe to execute within the listed guidelines; False otherwise.
        """

        # block command substitution anywhere
        for pattern in COMMAND_SUBSTITUTION_PATTERNS:
            if re.search(pattern, cmd):
                return False

        # validate each pipeline stage
        stages = [s.strip() for s in cmd.split("|")]

        for stage in stages:
            lowered = stage.lower()

            # check dangerous commands only at start of stage
            for pattern in DANGEROUS_PATTERNS + NETWORK_PATTERNS:
                if re.search(pattern, lowered):
                    return False

        # ensure first token is a real command
        try:
            first_stage = stages[0]
            parts = shlex.split(first_stage)
            if not parts:
                return False
        except Exception:
            return False

        return True
