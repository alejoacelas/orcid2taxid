import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_file: Optional path to a log file. If not provided, logs will only go to stderr.
        level: The logging level to use. Defaults to INFO.
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Always add stderr handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optionally add file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set more verbose logging for requests library
    logging.getLogger('urllib3').setLevel(logging.WARNING) 