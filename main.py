"""
Orchestrates the workflow of importing user data, identifying due/overdue insurance,
and sending notifications via SMS. Handles command-line arguments for controlling
notification behavior, test mode, and days-ahead checking.
"""

import sys
from datetime import datetime
from app.services.database import DatabaseService
from app.services.excel_service import ExcelService
from app.services.insurance_service import InsuranceService
from app.services.notification_service import NotificationService
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import DatabaseError, DataImportError, NotificationError
from app.utils.logger import setup_logger
from app.utils.decorators import log_operation
from app.utils.cli import parse_arguments
from app.utils.display import display_user_info, show_notification_mode, show_sms_count

# Configure logging
logger = setup_logger(__name__)


@log_operation("Main application")
def main():
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
            
            # Initialize insurance service with repository
            insurance_service = InsuranceService(user_repository, users)
            display_user_info(insurance_service)
            
            # Check for upcoming insurance and send SMS if requested
            if args.sms:
                test_mode = not args.prod
                show_notification_mode(test_mode)
                
                notification_service = NotificationService(user_repository, test_mode)
                sms_count = notification_service.check_upcoming_insurance(args.days)
                show_sms_count(sms_count)
            
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
