import logging
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# Use CET for log filename
cet_now = datetime.now(ZoneInfo("Europe/Paris"))
log_filename = f"schedular_{cet_now.strftime('%Y%m%d_%H%M%S')}.log"
log_path = log_dir / log_filename

# 👇 Ensure ALL log timestamps are in Paris (CET/CEST)
logging.Formatter.converter = lambda *args: datetime.now(ZoneInfo("Europe/Paris")).timetuple()

def setup_logger(name):
    """
    Configure and return a logger instance

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent adding duplicate handlers
    if logger.hasHandlers():
        return logger

    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1))
    console_handler.setLevel(logging.INFO)

    # Formatter: time will always be Paris time due to converter override above
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Create the logger instance
logger = setup_logger("taowar-scheduler")

# Add a startup message
logger.info("Logger initialized ✅")
