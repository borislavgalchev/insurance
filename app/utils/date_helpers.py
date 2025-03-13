"""
  - Role: Date manipulation and comparison utilities
  - Key Functions: Date parsing, formatting, and range calculations

Provides specialized date parsing, formatting, and calculation capabilities
needed for insurance due date processing. Includes DateRange class for
working with date periods and determining if dates fall within ranges.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Union
import pandas as pd
from config.settings import DATE_FORMAT
from app.utils.decorators import log_operation

def parse_date(date_input) -> Optional[date]:
    """
    Parse a date input according to the configured date format
    
    Args:
        date_input: Date input (can be string, date object, or pandas timestamp)
        
    Returns:
        date: Parsed date object or None if invalid
    """
    if date_input is None or pd.isna(date_input):
        return None
    
    try:
        # Already a date object
        if isinstance(date_input, date):
            return date_input
            
        # Handle pandas Timestamp
        if hasattr(date_input, 'date') and callable(getattr(date_input, 'date')):
            return date_input.date()
            
        # Convert to string and parse
        return datetime.strptime(str(date_input).strip(), DATE_FORMAT).date()
    except (ValueError, TypeError):
        return None


def get_upcoming_dates(reference_date: date, days_ahead: int = 5) -> date:
    """
    Calculate a date x days in the future from a reference date
    
    Args:
        reference_date: The starting date
        days_ahead: Number of days to add
        
    Returns:
        date: A date x days in the future
    """
    return reference_date + timedelta(days=days_ahead)


def format_date(date_obj: Optional[date]) -> str:
    """
    Format a date object according to the configured date format
    
    Args:
        date_obj: Date object to format
        
    Returns:
        str: Formatted date string
    """
    if not date_obj:
        return ""
    return date_obj.strftime(DATE_FORMAT)


def date_range(start_date: date, end_date: date) -> List[date]:
    """
    Generate a list of dates in a given range
    
    Args:
        start_date: Start date of the range
        end_date: End date of the range
        
    Returns:
        List[date]: List of dates in the range
    """
    if start_date > end_date:
        return []
        
    days = (end_date - start_date).days + 1
    return [start_date + timedelta(days=i) for i in range(days)]


class DateRange:
    """
    Class to represent and manipulate a date range
    """
    def __init__(self, start_date: date, end_date: date = None, days: int = None):
        """
        Initialize a date range
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range (optional if days is provided)
            days: Number of days in the range (optional if end_date is provided)
        """
        self.start_date = start_date
        
        if end_date is not None:
            self.end_date = end_date
        elif days is not None:
            self.end_date = start_date + timedelta(days=days)
        else:
            self.end_date = start_date
    
    def contains(self, check_date: date) -> bool:
        """
        Check if a date is within the range
        
        Args:
            check_date: Date to check
            
        Returns:
            bool: True if the date is within the range, False otherwise
        """
        return self.start_date <= check_date <= self.end_date
    
    def days_between(self) -> int:
        """
        Get the number of days between start and end date
        
        Returns:
            int: Number of days in the range
        """
        return (self.end_date - self.start_date).days
    
    def get_dates(self) -> List[date]:
        """
        Get all dates in the range
        
        Returns:
            List[date]: List of all dates in the range
        """
        return date_range(self.start_date, self.end_date)
    
    def __str__(self) -> str:
        """String representation of the date range"""
        return f"{format_date(self.start_date)} to {format_date(self.end_date)}"
