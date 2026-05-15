import logging
from pathlib import Path

BASE_DIR = Path.home() / ".bluegill"
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(session_id: str) -> logging.Logger:
    """
    Returns a session-specific logger writing to:
    ~/.bluegill/logs/{session_id}.log
    """

    logger = logging.getLogger(f"agent_{session_id}")
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs
    logger.propagate = False

    log_file = LOG_DIR / f"{session_id}.log"

    # Avoid duplicate handlers safely
    if not any(
        isinstance(h, logging.FileHandler)
        and getattr(h, "baseFilename", None) == str(log_file)
        for h in logger.handlers
    ):
        handler = logging.FileHandler(log_file, mode="a")

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger
