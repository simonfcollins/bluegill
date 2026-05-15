from pathlib import Path

"""
Simple resource loader for the system prompt.
"""

SYSTEM_PROMPT_PATH = Path(__file__).parent / "SYSTEM_PROMPT.md"

with open(SYSTEM_PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()
