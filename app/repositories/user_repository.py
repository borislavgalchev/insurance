"""
    - Role: Data access for user records

    - Key Functions:
    - create_table(): Sets up database schema
    - get_users_by_date_range(): Finds users with due dates in a period
    - get_upcoming_insurance_users(): Identifies users needing notifications

Provides specialized operations for retrieving users based on insurance criteria,
including due date ranges, notice periods, and overdue status. Implements
table creation and standard CRUD operations for User records.
"""

from typing import List, Optional
from datetime import date, timedelta
import logging
from app.models.user import User
from app.services.database import DatabaseService
from app.utils.repository import BaseRepository
from app.utils.decorators import log_operation

# Configure logging
logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Repository for user data access operations
    """
    def __init__(self, db_service: DatabaseService):
        """
        Initialize with database service
        
        Args:
            db_service: Database service instance
        """
        super().__init__(db_service, "users", User)
        self.create_table()
    
    def create_table(self) -> None:
        """
        Create users table if it doesn't exist
        
        Raises:
            DatabaseError: If table creation fails
        """
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nickname VARCHAR(255),
            full_name VARCHAR(255),
            cell_phone VARCHAR(100),
            car_type VARCHAR(100),
            license_plate VARCHAR(50),
            due_month DATE,
            notice DATE,
            due_day DATE,
            made_on DATE,
            amount INT,
            installments INT,
            policy_number VARCHAR(100)
        )
        """
        self.db.create_table(query)
    
    @log_operation("Get users by date range")
    def get_users_by_date_range(self, start_date: date, end_date: date) -> List[User]:
        """
        Get users with due dates in a specific range
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            List[User]: List of users with due dates in the range
        """
        query = """
        SELECT * FROM users
        WHERE due_day BETWEEN %s AND %s
        ORDER BY due_day ASC
        """
        return self.get_by_query(query, (start_date, end_date))
    
    @log_operation("Get users by notice date")
    def get_users_by_notice_date(self, notice_date: date) -> List[User]:
        """
        Get users with a specific notice date
        
        Args:
            notice_date: The notice date to search for
            
        Returns:
            List[User]: List of users with the given notice date
        """
        query = """
        SELECT * FROM users
        WHERE notice = %s
        ORDER BY due_day ASC
        """
        return self.get_by_query(query, (notice_date,))
        
    @log_operation("Get upcoming insurance users")
    def get_upcoming_insurance_users(self, start_date: date, end_date: date, notice_date: date) -> List[User]:
        """
        Get users with due dates in a specific range or specific notice date
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range
            notice_date: Notice date to check
            
        Returns:
            List[User]: List of users matching the criteria
        """
        query = """
        SELECT * FROM users
        WHERE due_day BETWEEN %s AND %s OR notice = %s
        ORDER BY due_day ASC
        """
        return self.get_by_query(query, (start_date, end_date, notice_date))
        
    @log_operation("Get users with due dates soon")
    def get_due_soon(self, days: int = 5) -> List[User]:
        """
        Get users with insurance due soon
        
        Args:
            days: Number of days ahead to check
            
        Returns:
            List[User]: List of users with insurance due soon
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        
        query = """
        SELECT * FROM users
        WHERE (notice IS NOT NULL AND notice BETWEEN %s AND %s)
        OR (due_day IS NOT NULL AND due_day BETWEEN %s AND %s)
        ORDER BY due_day ASC
        """
        return self.get_by_query(query, (today, end_date, today, end_date))
        
    @log_operation("Get users with overdue insurance")
    def get_overdue(self) -> List[User]:
        """
        Get users with overdue insurance
        
        Returns:
            List[User]: List of users with overdue insurance
        """
        today = date.today()
        
        query = """
        SELECT * FROM users
        WHERE due_day IS NOT NULL AND due_day < %s
        ORDER BY due_day ASC
        """
        return self.get_by_query(query, (today,))