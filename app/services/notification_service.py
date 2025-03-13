"""
  - Role: SMS notification delivery service
  - Key Functions:
    - send_sms(): Delivers messages via Twilio
    - check_upcoming_insurance(): Processes and notifies users

Manages the creation and delivery of payment reminder messages to customers,
handles notification scheduling based on due dates, and supports test mode
for verification without sending actual messages. Includes detailed logging
of notification attempts and delivery status.
"""

import logging
from datetime import date, timedelta
from typing import Optional, List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.utils.exceptions import NotificationError
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.utils.date_helpers import format_date
from config.settings import TWILIO_CONFIG, TEST_PHONE

# Configure logging
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending SMS notifications to users
    """
    def __init__(self, user_repository: UserRepository, test_mode: bool = True):
        """
        Initialize with user repository and test mode
        
        Args:
            user_repository: Repository for user data access
            test_mode: If True, send all SMS to the test phone number
        """
        self.user_repository = user_repository
        self.test_mode = test_mode
        self.today = date.today()
        
        # Initialize Twilio client if auth token is provided
        if TWILIO_CONFIG.get('auth_token'):
            self.client = Client(TWILIO_CONFIG['account_sid'], TWILIO_CONFIG['auth_token'])
        else:
            self.client = None
            logger.warning("Twilio client not initialized: auth_token not provided")
            
        # Log mode
        logger.info(f"Notification service initialized in {'TEST' if test_mode else 'PRODUCTION'} mode")
        if test_mode:
            logger.info(f"Test phone number: {TEST_PHONE}")
    
    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number format for Twilio
        
        Args:
            phone: Phone number to normalize
            
        Returns:
            str: Normalized phone number
        """
        if not phone:
            return ""
            
        # Remove spaces, dashes, and parentheses
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Ensure it starts with a plus sign and country code
        if not cleaned.startswith('+'):
            # Assume Bulgarian number if no country code
            if cleaned.startswith('0'):
                cleaned = '+359' + cleaned[1:]
            else:
                cleaned = '+' + cleaned
                
        return cleaned
    
    def send_sms(self, to_number: str, message_body: str) -> Optional[str]:
        """
        Send an SMS message
        
        Args:
            to_number: Recipient phone number
            message_body: Message content
            
        Returns:
            Optional[str]: Message SID if sent successfully, None otherwise
            
        Raises:
            NotificationError: If SMS sending fails
        """
        if not self.client:
            logger.warning("Twilio client not initialized. SMS not sent.")
            if self.test_mode:
                logger.info(f"TEST MODE: Would send to {to_number}: {message_body}")
                return "test_message_id"
            return None
            
        # Normalize phone number
        to_number = self.normalize_phone(to_number)
        
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
            
            # Deduplicate the user list
            unique_users = deduplicate_users(upcoming_users)
            
            sms_sent_count = 0
            
            if unique_users:
                logger.info(f"Found {len(unique_users)} unique users with upcoming insurance dates (from {len(upcoming_users)} total records)")
                
                for user in unique_users:
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