import logging
import os

def setup_logger(name="x_agent_logger", log_file="x_agent.log"):
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # Console handler (optional, for real-time feedback)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s] %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Avoid duplicate handlers if re-imported
    if not logger.hasHandlers():
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

# Usage: from logger import setup_logger; logger = setup_logger(__name__)
