"""
Decorators for common functionality across the application
"""
import functools
import logging
from typing import Any, Callable, TypeVar, cast
import mysql.connector
from app.utils.exceptions import DatabaseError

T = TypeVar('T')

def db_operation(operation_name: str) -> Callable:
    """
    Decorator for database operations to standardize error handling
    
    Args:
        operation_name: Name of the operation for logging
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = logging.getLogger(func.__module__)
            try:
                return func(*args, **kwargs)
            except mysql.connector.Error as err:
                logger.error(f"{operation_name} failed: {err}")
                # Get self.conn for rollback if available
                if len(args) > 0 and hasattr(args[0], 'conn'):
                    try:
                        args[0].conn.rollback()
                    except:
                        pass  # Ignore rollback errors
                raise DatabaseError(f"{operation_name} failed: {err}")
        return cast(Callable[..., T], wrapper)
    return decorator

def log_operation(operation_name: str) -> Callable:
    """
    Decorator for logging function execution
    
    Args:
        operation_name: Name of the operation for logging
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = logging.getLogger(func.__module__)
            logger.debug(f"Starting {operation_name}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Completed {operation_name}")
                return result
            except Exception as err:
                logger.error(f"Error in {operation_name}: {err}")
                raise
        return cast(Callable[..., T], wrapper)
    return decorator