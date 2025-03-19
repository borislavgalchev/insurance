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
from app.utils.exceptions import DatabaseError

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
            policy_number VARCHAR(100),
            UNIQUE KEY unique_insurance_policy (full_name, due_day, policy_number),
            INDEX idx_full_name (full_name),
            INDEX idx_due_day (due_day),
            INDEX idx_notice (notice)
        )
        """
        self.db.create_table(query)
        
        # This might fail if the table already exists with existing data.
        # In that case, we need to alter the table and add the constraints.
        try:
            # Check if table exists but doesn't have the constraints
            query = """
            SELECT COUNT(*) as count FROM information_schema.TABLE_CONSTRAINTS 
            WHERE CONSTRAINT_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'users' 
            AND CONSTRAINT_NAME = 'unique_insurance_policy'
            """
            
            result = self.db.fetch_one(query)
            
            if result and result.get('count', 0) == 0:
                # Add the unique constraint if it doesn't exist
                query = """
                ALTER TABLE users 
                ADD CONSTRAINT unique_insurance_policy 
                UNIQUE (full_name, due_day, policy_number)
                """
                self.db.execute_query(query)
                
                # Add indexes if they don't exist
                self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_full_name ON users (full_name)")
                self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_due_day ON users (due_day)")
                self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_notice ON users (notice)")
                
                logger.info("Added unique constraint and indexes to users table")
        except Exception as e:
            logger.warning(f"Could not add unique constraint: {e}. This is expected if constraints already exist.")
    
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
        SELECT DISTINCT full_name, due_day, notice, cell_phone, car_type, license_plate,
                      nickname, due_month, made_on, amount, installments, policy_number, id
        FROM users
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
        SELECT DISTINCT full_name, due_day, notice, cell_phone, car_type, license_plate,
                      nickname, due_month, made_on, amount, installments, policy_number, id
        FROM users
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
        SELECT DISTINCT full_name, due_day, notice, cell_phone, car_type, license_plate,
                      nickname, due_month, made_on, amount, installments, policy_number, id
        FROM users
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
        SELECT DISTINCT full_name, due_day, notice, cell_phone, car_type, license_plate,
                      nickname, due_month, made_on, amount, installments, policy_number, id
        FROM users
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
        SELECT DISTINCT full_name, due_day, notice, cell_phone, car_type, license_plate,
                      nickname, due_month, made_on, amount, installments, policy_number, id
        FROM users
        WHERE due_day IS NOT NULL AND due_day < %s
        ORDER BY due_day ASC
        """
        return self.get_by_query(query, (today,))
        
    @log_operation("Check for duplicate user")
    def check_duplicate(self, user: User) -> bool:
        """
        Check if a user record already exists based on unique constraint fields
        
        Args:
            user: User object to check for duplicates
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        query = """
        SELECT COUNT(*) as count FROM users
        WHERE full_name = %s AND due_day = %s AND policy_number = %s
        """
        
        result = self.db.fetch_one(query, (user.full_name, user.due_day, user.policy_number))
        
        return result and result.get('count', 0) > 0