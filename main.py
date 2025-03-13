import sys
import argparse
from datetime import datetime
from app.services.database import DatabaseService
from app.services.excel_service import ExcelService
from app.services.insurance_service import InsuranceService
from app.services.notification_service import NotificationService
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import DatabaseError, DataImportError, NotificationError
from app.utils.logger import setup_logger
from app.utils.decorators import log_operation
from config.settings import DEFAULT_EXCEL_PATH, NOTIFICATION_DAYS_AHEAD

# Configure logging
logger = setup_logger(__name__)


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Insurance Management System')
    parser.add_argument('--sms', action='store_true', help='Check upcoming insurance and send SMS')
    parser.add_argument('--prod', action='store_true', help='Run in production mode (send to real numbers)')
    parser.add_argument('--days', type=int, default=NOTIFICATION_DAYS_AHEAD, 
                        help='Number of days ahead to check for due dates')
    parser.add_argument('--excel', type=str, default=DEFAULT_EXCEL_PATH,
                        help='Path to the Excel file')
    
    # For backward compatibility, also check sys.argv
    args = parser.parse_args()
    if not args.sms and 'sms' in sys.argv:
        args.sms = True
    if not args.prod and 'prod' in sys.argv:
        args.prod = True
        
    return args


@log_operation("Display user information")
def display_user_info(insurance_service):
    """
    Display information about users
    
    Args:
        insurance_service: Insurance service instance
    """
    # Get users due soon and overdue
    due_soon = insurance_service.get_due_soon()
    overdue = insurance_service.get_overdue()
    
    # Print results
    logger.info(f"Found {len(due_soon)} users due soon")
    print("\nUsers due soon:")
    for user in due_soon:
        print(f"{user.full_name} - Due: {user.due_day} - Notice: {user.notice}")
    
    logger.info(f"Found {len(overdue)} overdue users")
    print("\nOverdue users:")
    for user in overdue:
        print(f"{user.full_name} - Due: {user.due_day}")

    # Sort by due date
    sorted_by_due = insurance_service.sort_by_date('due_day')
    print("\nSorted by due date (first 5):")
    for user in sorted_by_due[:5]:
        print(f"{user.full_name} - Due: {user.due_day}")


@log_operation("Main application")
def main():
    """
    Main function
    """
    args = parse_arguments()
    db_service = None
    
    try:
        # Initialize database service
        db_service = DatabaseService()
        
        # Initialize user repository
        user_repository = UserRepository(db_service)
        
        # Process Excel data
        try:
            excel_service = ExcelService(args.excel)
            users = excel_service.get_users()
            
            # Insert users into database
            for user in users:
                user_repository.insert(user)
            
            # Initialize insurance service
            insurance_service = InsuranceService(users)
            display_user_info(insurance_service)
            
            # Check for upcoming insurance and send SMS if requested
            if args.sms:
                test_mode = not args.prod
                mode_text = "TEST MODE" if test_mode else "PRODUCTION MODE"
                
                print("\n" + "=" * 50)
                print(f"CHECKING UPCOMING INSURANCE AND SENDING SMS NOTIFICATIONS ({mode_text})")
                print("=" * 50 + "\n")
                
                notification_service = NotificationService(user_repository, test_mode)
                sms_count = notification_service.check_upcoming_insurance(args.days)
                print(f"\nTotal SMS messages sent: {sms_count}")
            
        except DataImportError as e:
            logger.error(f"Error importing data: {e}")
            sys.exit(1)
        except NotificationError as e:
            logger.error(f"Error sending notifications: {e}")
    
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Always close database connection
        if db_service:
            db_service.close()


if __name__ == "__main__":
    main()