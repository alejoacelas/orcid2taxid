import logging
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict
from logging import Logger, Formatter, StreamHandler, FileHandler, INFO, WARNING, ERROR, getLogger
from functools import wraps

# Define logger hierarchy
LOGGER_HIERARCHY = {
    'orcid2taxid': {
        'core': {
            'integrations': {
                'orcid': None,
                'ncbi': None,
                'nsf': None,
                'nih': None,
                'epmc': None,
                'unpaywall': None
            },
            'utils': {
                'llm': None,
                'date': None
            }
        }
    }
}

class LogConfig:
    """Configuration for logging system"""
    def __init__(self):
        self.log_dir = Path(__file__).parents[4] / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.disabled_loggers: Dict[str, bool] = {
            'orcid2taxid.core.utils.llm': True  # Disable LLM logging by default
        }
        
    def disable_logger(self, logger_name: str) -> None:
        """Disable a specific logger"""
        self.disabled_loggers[logger_name] = True
        
    def enable_logger(self, logger_name: str) -> None:
        """Enable a specific logger"""
        self.disabled_loggers[logger_name] = False
        
    def is_logger_enabled(self, logger_name: str) -> bool:
        """Check if a logger is enabled"""
        return not self.disabled_loggers.get(logger_name, False)

# Global logging configuration
log_config = LogConfig()

def get_logger(module_name: str) -> Logger:
    """
    Get a logger for a module with proper hierarchy.
    
    Args:
        module_name: Full module path (e.g., 'orcid2taxid.core.integrations.orcid')
    
    Returns:
        Configured logger instance
    """
    logger = getLogger(module_name)
    
    # Only set up handlers if this is the first time getting this logger
    if not logger.handlers:
        setup_logger(logger, module_name)
    
    return logger

def setup_logger(logger: Logger, module_name: str) -> None:
    """Set up handlers and formatters for a logger"""
    formatter = Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(INFO)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = log_config.log_dir / f"{module_name.replace('.', '_')}.log"
    file_handler = FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(INFO)
    logger.addHandler(file_handler)
    
    # Set logger level
    logger.setLevel(INFO)
    logger.propagate = False

def log_event(logger_name: str):
    """
    Decorator for logging function entry/exit and errors.
    Usage:
        @log_event('orcid2taxid.core.integrations.orcid')
        async def some_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            if not log_config.is_logger_enabled(logger_name):
                return await func(*args, **kwargs)
                
            try:
                logger.info(f"Starting {func.__name__}")
                result = await func(*args, **kwargs)
                logger.info(f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            if not log_config.is_logger_enabled(logger_name):
                return func(*args, **kwargs)
                
            try:
                logger.info(f"Starting {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Initialize logging for all modules in hierarchy
def initialize_logging():
    """Initialize logging for all modules in the hierarchy"""
    def setup_hierarchy(hierarchy: dict, prefix: str = ''):
        for name, children in hierarchy.items():
            full_name = f"{prefix}.{name}" if prefix else name
            if children is None:
                get_logger(full_name)
            else:
                setup_hierarchy(children, full_name)
    
    setup_hierarchy(LOGGER_HIERARCHY)
    
    # Set up third-party loggers
    getLogger('urllib3').setLevel(WARNING)
    getLogger('httpx').setLevel(WARNING)

# Initialize logging on module import
initialize_logging() 