"""
  - Role: Custom exception types
  - Contents: DatabaseError, NotificationError, ValidationError
"""

class DatabaseError(Exception):
    """Exception raised for database-related errors"""
    pass


class DataImportError(Exception):
    """Exception raised for errors during data import"""
    pass


class NotificationError(Exception):
    """Exception raised for errors during notification sending"""
    pass


class ValidationError(Exception):
    """Exception raised for validation errors"""
    pass


class ResourceNotFoundError(Exception):
    """Exception raised when a requested resource is not found"""
    pass


class AuthenticationError(Exception):
    """Exception raised for authentication failures"""
    pass
