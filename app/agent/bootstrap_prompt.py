from pathlib import Path

BOOTSTRAP_PROMPT_PATH = Path(__file__).parent / "BOOTSTRAP.txt"

with open(BOOTSTRAP_PROMPT_PATH, "r") as f:
    BOOTSTRAP_PROMPT = f.read()