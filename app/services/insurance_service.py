from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import logging
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)


class InsuranceService:
    """
    Service for insurance-related business logic
    """
    def __init__(self, users: List[User] = None):
        """
        Initialize with a list of users
        
        Args:
            users: List of User objects (optional)
        """
        self.users = users or []
        self.today = datetime.now().date()
    
    def set_users(self, users: List[User]) -> None:
        """
        Set the list of users
        
        Args:
            users: List of User objects
        """
        self.users = users
    
    def sort_by_date(self, date_field: str) -> List[User]:
        """
        Sort users by a date field
        
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
        Get users with insurance due soon
        
        Args:
            days: Number of days ahead to check
            
        Returns:
            List[User]: List of users with insurance due soon
        """
        due_soon = []
        
        for user in self.users:
            if user.due_day and user.notice:
                due_date = user.due_day
                notice_date = user.notice
                
                # Check if within n days of notice date
                notice_window = notice_date + timedelta(days=days)
                if self.today <= notice_window and self.today >= notice_date:
                    due_soon.append(user)
                # Check if past due date
                elif self.today > due_date:
                    due_soon.append(user)
        
        logger.info(f"Found {len(due_soon)} users with insurance due soon")
        return due_soon
    
    def get_overdue(self) -> List[User]:
        """
        Get users with overdue insurance
        
        Returns:
            List[User]: List of users with overdue insurance
        """
        overdue = [user for user in self.users if user.due_day and self.today > user.due_day]
        logger.info(f"Found {len(overdue)} users with overdue insurance")
        return overdue