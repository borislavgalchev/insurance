"""
Centralized logging configuration
"""
import logging
from typing import Optional

# Default logging format
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_LEVEL = logging.INFO

def setup_logger(
    name: Optional[str] = None, 
    level: int = DEFAULT_LEVEL,
    format_str: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT
) -> logging.Logger:
    """
    Configure and return a logger
    
    Args:
        name: Logger name (default: root logger)
        level: Logging level
        format_str: Log format string
        date_format: Date format string
        
    Returns:
        logging.Logger: Configured logger
    """
    # Get the logger
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set level
        logger.setLevel(level)
        
        # Create handler for console output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(format_str, date_format)
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
    return logger