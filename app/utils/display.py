"""
Display utilities for the Insurance Management System.

Provides functions for formatting and displaying information to the user
in a consistent manner. Separates UI concerns from business logic and
application flow control.
"""

import logging
from app.utils.decorators import log_operation

# Configure logging
logger = logging.getLogger(__name__)


@log_operation("Display user information")
def display_user_info(insurance_service):
    """
    Display information about users with due and overdue insurance
    
    Args:
        insurance_service: Insurance service instance
    """
    # Get users due soon and overdue
    due_soon = insurance_service.get_due_soon()
    overdue = insurance_service.get_overdue()
    
    # Deduplicate users based on name and due date
    def deduplicate_users(users):
        seen = set()
        unique_users = []
        
        for user in users:
            # Create a unique key based on name and due date
            key = (user.full_name, str(user.due_day))
            
            if key not in seen:
                seen.add(key)
                unique_users.append(user)
                
        return unique_users
    
    # Deduplicate the lists
    unique_due_soon = deduplicate_users(due_soon)
    unique_overdue = deduplicate_users(overdue)
    
    # Print results
    logger.info(f"Found {len(unique_due_soon)} unique users with insurance due soon (from {len(due_soon)} total records)")
    print("\nUsers due soon:")
    for user in unique_due_soon:
        print(f"{user.full_name} - Due: {user.due_day} - Notice: {user.notice}")
    
    logger.info(f"Found {len(unique_overdue)} unique users with overdue insurance (from {len(overdue)} total records)")
    print("\nOverdue users:")
    for user in unique_overdue:
        print(f"{user.full_name} - Due: {user.due_day}")

    # Sort by due date and deduplicate
    all_users = deduplicate_users(insurance_service.sort_by_date('due_day'))
    print("\nSorted by due date (first 5):")
    for user in all_users[:5]:
        print(f"{user.full_name} - Due: {user.due_day}")


def show_notification_mode(test_mode):
    """
    Display the notification mode banner
    
    Args:
        test_mode: Boolean indicating if running in test mode
    """
    mode_text = "TEST MODE" if test_mode else "PRODUCTION MODE"
    
    print("\n" + "=" * 50)
    print(f"CHECKING UPCOMING INSURANCE AND SENDING SMS NOTIFICATIONS ({mode_text})")
    print("=" * 50 + "\n")


def show_sms_count(count):
    """
    Display the total SMS count
    
    Args:
        count: Number of SMS messages sent
    """
    print(f"\nTotal SMS messages sent: {count}")