from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime, date, timedelta
import logging
from typing import List, Optional
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.date_helpers import format_date
from app.utils.exceptions import NotificationError
from config.settings import TWILIO_CONFIG, TEST_PHONE, DATE_FORMAT

# Configure logging
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications to users
    """
    def __init__(self, user_repository: UserRepository, test_mode: bool = True):
        """
        Initialize with user repository and test mode
        
        Args:
            user_repository: User repository instance
            test_mode: Whether to run in test mode (send to test phone)
        """
        self.user_repository = user_repository
        self.test_mode = test_mode
        self.today = datetime.now().date()
        self.sms_enabled = True
        
        # Validate Twilio configuration
        if not TWILIO_CONFIG.get('account_sid') or not TWILIO_CONFIG.get('auth_token'):
            logger.warning("Twilio credentials not found in environment variables. SMS functionality will be disabled.")
            self.sms_enabled = False
            return
            
        if not TWILIO_CONFIG.get('phone_number'):
            logger.warning("Twilio phone number not found in environment variables. SMS functionality will be disabled.")
            self.sms_enabled = False
            return
            
        if self.test_mode and not TEST_PHONE:
            logger.warning("Test phone number not found in environment variables.")
        
        # Set up Twilio client
        try:
            self.client = Client(
                TWILIO_CONFIG['account_sid'],
                TWILIO_CONFIG['auth_token']
            )
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.sms_enabled = False
            logger.warning("SMS functionality will be disabled.")
    
    def send_sms(self, to_number: str, message_body: str) -> Optional[str]:
        """
        Send SMS using Twilio
        
        Args:
            to_number: Phone number to send SMS to
            message_body: Message content
            
        Returns:
            str: Message SID if successful, None otherwise
            
        Raises:
            NotificationError: If sending fails
        """
        # Skip sending if SMS is disabled
        if not self.sms_enabled:
            logger.warning("SMS functionality is disabled. Message not sent.")
            return None
            
        # Skip sending if the phone number is invalid
        if not to_number or to_number == '*' or len(to_number) < 10:
            logger.warning(f"Invalid phone number: {to_number}. SMS not sent.")
            return None
        
        try:
            message = self.client.messages.create(
                from_=TWILIO_CONFIG['phone_number'],
                body=message_body,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number}. Message SID: {message.sid}")
            return message.sid
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e}")
            raise NotificationError(f"Failed to send SMS: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            raise NotificationError(f"Failed to send SMS: {e}")
    
    def check_upcoming_insurance(self, days_ahead: int = 5) -> int:
        """
        Check for upcoming insurance due dates and send SMS notifications
        
        Args:
            days_ahead: Number of days ahead to check for due dates
            
        Returns:
            int: Number of SMS messages sent
            
        Raises:
            NotificationError: If checking fails
        """
        try:
            future_date = self.today + timedelta(days=days_ahead)
            
            logger.info(f"Checking for users with due dates between {self.today} and {future_date}")
            
            # Get users with upcoming insurance
            upcoming_users = self.user_repository.get_upcoming_insurance_users(
                self.today, future_date, self.today
            )
            
            sms_sent_count = 0
            
            if upcoming_users:
                logger.info(f"Found {len(upcoming_users)} users with upcoming insurance dates")
                
                for user in upcoming_users:
                    days_until_due = (user.due_day - self.today).days if user.due_day else 0
                    
                    # Determine if we should send an SMS based on due date or notice date
                    message = None
                    
                    if user.notice == self.today:
                        message = (f"Hello {user.full_name}, this is a reminder that your insurance "
                                  f"for {user.car_type} ({user.license_plate}) will be due on "
                                  f"{format_date(user.due_day)}.")
                    elif user.due_day == self.today:
                        message = (f"Hello {user.full_name}, your insurance for {user.car_type} "
                                  f"({user.license_plate}) is due TODAY. Please make your payment as soon as possible.")
                    
                    if message:
                        # In test mode, send all SMS to the test phone number
                        # In production mode, use the user's actual phone number
                        phone_number = TEST_PHONE if self.test_mode else user.cell_phone
                        
                        # Log user details
                        logger.info(f"User: {user.full_name}")
                        logger.info(f"Due: {user.due_day} (in {days_until_due} days)")
                        logger.info(f"Vehicle: {user.car_type} ({user.license_plate})")
                        logger.info(f"Phone: {phone_number if self.test_mode else user.cell_phone}")
                        
                        try:
                            message_sid = self.send_sms(phone_number, message)
                            if message_sid:
                                logger.info(f"SMS sent successfully. Message SID: {message_sid}")
                                sms_sent_count += 1
                        except NotificationError:
                            # Already logged in send_sms, just continue with the next user
                            continue
            else:
                logger.info("No users with upcoming insurance dates found.")
            
            return sms_sent_count
        
        except Exception as e:
            logger.error(f"Error checking upcoming insurance: {e}")
            raise NotificationError(f"Error checking upcoming insurance: {e}")