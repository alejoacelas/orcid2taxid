import logging
import sys
from pathlib import Path
from typing import Optional
from logging import Logger, Formatter, StreamHandler, FileHandler, INFO, WARNING, getLogger

def get_default_log_dir() -> Path:
    """Get the default logging directory."""
    # Get the project root directory (assuming src/orcid2taxid is in project root)
    project_root = Path(__file__).parents[4]  # Adjust number based on file location
    return project_root / 'logs'

def get_module_log_file(module_name: str) -> Path:
    """
    Get the log file path for a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'orcid_client')
    
    Returns:
        Path object pointing to the log file
    """
    log_dir = get_default_log_dir()
    
    # Create logs directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a log file named after the module
    return log_dir / f"{module_name}.log"

def get_logger(module_name: str) -> Logger:
    """
    Set up logging for a module and return its logger.
    This is a convenience function that handles all logging setup in one call.
    
    Args:
        module_name: Name of the module (e.g., 'orcid_client')
    
    Returns:
        Logger instance configured for the module
    """
    log_file = get_module_log_file(module_name)
    setup_logging(log_file=log_file)
    logger = getLogger(module_name)
    logger.setLevel(INFO)  # Ensure module logger is set to INFO
    return logger

def setup_logging(log_file: Optional[Path] = None, level: int = INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_file: Optional path to a log file. If not provided, logs will only go to stderr.
        level: The logging level to use. Defaults to INFO.
    """
    # Create formatter
    formatter = Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure root logger
    root_logger = getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Always add stderr handler
    console_handler = StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)  # Set level for console handler
    root_logger.addHandler(console_handler)

    # Optionally add file handler
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)  # Set level for file handler
        root_logger.addHandler(file_handler)

    # Set more verbose logging for requests library
    getLogger('urllib3').setLevel(WARNING) 