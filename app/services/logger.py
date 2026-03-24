import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)  # ensure the logs directory exists

def get_logger(session_id: str) -> logging.Logger:
    """
    Returns a logger instance for a given session ID.
    Each session gets its own log file: logs/{session_id}.log
    """
    logger = logging.getLogger(f"agent_{session_id}")
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if logger already exists
    if not logger.handlers:
        log_file = LOG_DIR / f"{session_id}.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger