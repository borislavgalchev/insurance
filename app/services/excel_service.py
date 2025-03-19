"""
  - Role: Imports user data from Excel files
  - Key Functions:
    - _rename_columns(): Translates column names from Bulgarian
    - get_users(): Extracts and converts user data

Processes Excel files containing customer records, translates column names
from Bulgarian to English, validates incoming data, and converts raw data
into User model instances. Handles date parsing and data type conversion.
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Set, Tuple
from app.models.user import User
from app.utils.date_helpers import parse_date
from app.utils.exceptions import DataImportError
from config.settings import BG_to_ENG

# Configure logging
logger = logging.getLogger(__name__)


class ExcelService:
    """
    Service for handling Excel data import
    """
    def __init__(self, file_path: str):
        """
        Initialize with the path to an Excel file
        
        Args:
            file_path: Path to the Excel file
            
        Raises:
            DataImportError: If file cannot be read
        """
        try:
            self.file_path = file_path
            self.df = pd.read_excel(file_path)
            self._rename_columns()
            logger.info(f"Successfully loaded Excel file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            raise DataImportError(f"Failed to load Excel file: {e}")
    
    def _rename_columns(self) -> None:
        """
        Rename columns from Bulgarian to English
        
        Raises:
            DataImportError: If columns cannot be renamed
        """
        try:
            rename_dict = {k: v for k, v in BG_to_ENG.items() if k in self.df.columns}
            self.df.rename(columns=rename_dict, inplace=True)
            logger.debug("Columns renamed successfully")
        except Exception as e:
            logger.error(f"Failed to rename columns: {e}")
            raise DataImportError(f"Failed to rename columns: {e}")
    
    def get_users(self) -> List[User]:
        """
        Extract user data from the Excel file
        
        Returns:
            List[User]: List of user objects
            
        Raises:
            DataImportError: If data cannot be processed
        """
        try:
            users = []
            # Track duplicates within the Excel file
            seen_records: Set[Tuple[str, str, str]] = set()
            duplicate_count = 0
            
            for _, row in self.df.iterrows():
                # Safe conversion for numeric fields
                try:
                    amount = int(row['amount']) if pd.notna(row['amount']) else 0
                except (ValueError, TypeError):
                    amount = 0
                    
                try:
                    installments = int(row['installments']) if pd.notna(row['installments']) else 0
                except (ValueError, TypeError):
                    installments = 0
                
                # Extract required fields for deduplication
                full_name = str(row['full_name']) if pd.notna(row['full_name']) else ''
                due_day = parse_date(row['due_day'])
                policy_number = str(row['policy_number']) if pd.notna(row['policy_number']) else ''
                
                # Skip empty records
                if not full_name or not due_day:
                    logger.warning(f"Skipping record with missing name or due date: {full_name}")
                    continue
                
                # Check for duplicates within the current Excel file
                record_key = (full_name, str(due_day), policy_number)
                if record_key in seen_records:
                    logger.info(f"Skipping duplicate record in Excel: {full_name}, {due_day}, {policy_number}")
                    duplicate_count += 1
                    continue
                
                seen_records.add(record_key)
                
                user_data = {
                    'nickname': str(row['nickname']) if pd.notna(row['nickname']) else '',
                    'full_name': full_name,
                    'cell_phone': str(row['cell_phone']) if pd.notna(row['cell_phone']) else '',
                    'car_type': str(row['car_type']) if pd.notna(row['car_type']) else '',
                    'license_plate': str(row['license_plate']) if pd.notna(row['license_plate']) else '',
                    'due_month': parse_date(row['due_month']),
                    'notice': parse_date(row['notice']),
                    'due_day': due_day,
                    'made_on': parse_date(row['made_on']),
                    'amount': amount,
                    'installments': installments,
                    'policy_number': policy_number
                }
                
                users.append(User.from_dict(user_data))
            
            if duplicate_count > 0:
                logger.info(f"Found and skipped {duplicate_count} duplicate records in Excel file")
            
            logger.info(f"Processed {len(users)} unique users from Excel file")
            return users
        except Exception as e:
            logger.error(f"Failed to process Excel data: {e}")
            raise DataImportError(f"Failed to process Excel data: {e}")