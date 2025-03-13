"""
  - Role: Core business logic
  - Key Functions:
    - get_due_soon(): Finds users with upcoming payments
    - get_overdue(): Identifies users with missed payments

Implements algorithms for identifying users with upcoming due dates,
overdue payments, and notice date requirements. Provides sorting and
filtering capabilities based on insurance-specific criteria.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging
from app.models.user import User
from app.repositories.user_repository import UserRepository

# Configure logging
logger = logging.getLogger(__name__)


class InsuranceService:
    """
    Service for insurance-related business logic
    """
    def __init__(self, user_repository: UserRepository, users: Optional[List[User]] = None):
        """
        Initialize with user repository and optional list of users
        
        Args:
            user_repository: Repository for user data access
            users: Optional list of User objects (for sorting and in-memory operations)
        """
        self.user_repository = user_repository
        self.users = users or []
        self.today = datetime.now().date()
    
    def set_users(self, users: List[User]) -> None:
        """
        Set the list of users for in-memory operations
        
        Args:
            users: List of User objects
        """
        self.users = users
    
    def sort_by_date(self, date_field: str) -> List[User]:
        """
        Sort users by a date field (in-memory operation)
        
        Args:
            date_field: Name of the date field to sort by
            
        Returns:
            List[User]: Sorted list of users
        """
        # Use a very future date for users without the specified date field
        max_date = datetime.max.date()
        
        def get_date(user):
            value = getattr(user, date_field)
            return value if value else max_date
            
        return sorted(self.users, key=get_date)
    
    def get_due_soon(self, days: int = 5) -> List[User]:
        """
        Get users with insurance due soon (delegates to repository)
        
        Args:
            days: Number of days ahead to check
            
        Returns:
            List[User]: List of users with insurance due soon
        """
        due_soon = self.user_repository.get_due_soon(days)
        logger.info(f"Found {len(due_soon)} users with insurance due soon")
        return due_soon
    
    def get_overdue(self) -> List[User]:
        """
        Get users with overdue insurance (delegates to repository)
        
        Returns:
            List[User]: List of users with overdue insurance
        """
        overdue = self.user_repository.get_overdue()
        logger.info(f"Found {len(overdue)} users with overdue insurance")
        return overdue