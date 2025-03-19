"""
  - Role: Viber notification delivery service
  - Key Functions:
    - send_message(): Delivers messages via Viber
    - check_upcoming_insurance(): Processes and notifies users

Manages the creation and delivery of payment reminder messages to customers,
handles notification scheduling based on due dates, and supports test mode
for verification without sending actual messages. Includes detailed logging
of notification attempts and delivery status.
"""

import logging
import uuid
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import TextMessage
from viberbot.api.viber_requests import ViberFailedRequest

from app.utils.exceptions import NotificationError
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.utils.date_helpers import format_date
from config.settings import VIBER_CONFIG, TEST_PHONE

# Configure logging
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending Viber notifications to users
    """
    def __init__(self, user_repository: UserRepository, test_mode: bool = True):
        """
        Initialize with user repository and test mode
        
        Args:
            user_repository: Repository for user data access
            test_mode: If True, send all messages to the test phone number
        """
        self.user_repository = user_repository
        self.test_mode = test_mode
        self.today = date.today()
        
        # Initialize Viber client if auth token is provided
        if VIBER_CONFIG.get('auth_token'):
            bot_configuration = BotConfiguration(
                auth_token=VIBER_CONFIG['auth_token'],
                name=VIBER_CONFIG['name'],
                avatar=VIBER_CONFIG['avatar']
            )
            self.viber = Api(bot_configuration)
            
            # Set the webhook URL if provided - this only needs to be done once
            # but we keep it here for completeness
            if VIBER_CONFIG.get('webhook_url'):
                try:
                    self.viber.set_webhook(VIBER_CONFIG['webhook_url'])
                    logger.info(f"Viber webhook set to {VIBER_CONFIG['webhook_url']}")
                except Exception as e:
                    logger.warning(f"Failed to set Viber webhook: {e}")
        else:
            self.viber = None
            logger.warning("Viber client not initialized: auth_token not provided")
            
        # Log mode
        logger.info(f"Notification service initialized in {'TEST' if test_mode else 'PRODUCTION'} mode")
        if test_mode:
            logger.info(f"Test phone number: {TEST_PHONE}")
    
    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number format for Viber
        
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
    
    def send_message(self, to_number: str, message_text: str) -> Optional[str]:
        """
        Send a Viber message
        
        Args:
            to_number: Recipient phone number
            message_text: Message content
            
        Returns:
            Optional[str]: Message ID if sent successfully, None otherwise
            
        Raises:
            NotificationError: If message sending fails
        """
        if not self.viber:
            logger.warning("Viber client not initialized. Message not sent.")
            if self.test_mode:
                logger.info(f"TEST MODE: Would send to {to_number}: {message_text}")
                return str(uuid.uuid4())  # Return a mock message ID
            return None
            
        # Normalize phone number
        to_number = self.normalize_phone(to_number)
        
        if not to_number or to_number == '*' or len(to_number) < 10:
            logger.warning(f"Invalid phone number: {to_number}. Message not sent.")
            return None
        
        try:
            # Create a text message
            message = TextMessage(
                text=message_text,
                tracking_data=f"insurance-notification-{date.today().isoformat()}"
            )
            
            # Send the message
            response = self.viber.send_messages(to_number, [message])
            
            # Generate a message ID (Viber doesn't return an ID like Twilio)
            message_id = str(uuid.uuid4())
            
            logger.info(f"Viber message sent to {to_number}. Message ID: {message_id}")
            return message_id
            
        except ViberFailedRequest as e:
            logger.error(f"Viber error: {e}")
            raise NotificationError(f"Failed to send Viber message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending Viber message: {e}")
            raise NotificationError(f"Failed to send Viber message: {e}")
    
    def format_viber_message(self, user: User, message_text: str) -> Dict[str, Any]:
        """
        Format a message for Viber
        
        Args:
            user: User to send message to
            message_text: Message content
            
        Returns:
            Dict[str, Any]: Formatted message
        """
        # Normalize phone
        phone = self.normalize_phone(user.cell_phone)
        if not phone:
            phone = 'UNKNOWN'
            
        return {
            "receiver": phone,
            "type": "text",
            "sender": {
                "name": VIBER_CONFIG['name'],
            },
            "text": message_text
        }
    
    def deduplicate_users(self, users: List[User]) -> List[User]:
        """
        Deduplicate users based on name, due date, and policy number
        
        Args:
            users: List of users to deduplicate
            
        Returns:
            List[User]: Deduplicated list of users
        """
        seen = set()
        unique_users = []
        
        for user in users:
            # Create a unique key based on name, due date, and policy number
            key = (user.full_name, str(user.due_day), user.policy_number)
            
            if key not in seen:
                seen.add(key)
                unique_users.append(user)
                
        return unique_users
    
    def check_upcoming_insurance(self, days_ahead: int = 5) -> int:
        """
        Check for upcoming insurance due dates and send Viber notifications
        
        Args:
            days_ahead: Number of days ahead to check for due dates
            
        Returns:
            int: Number of messages sent
            
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
            
            # Deduplicate the user list
            unique_users = self.deduplicate_users(upcoming_users)
            
            messages_sent_count = 0
            
            if unique_users:
                logger.info(f"Found {len(unique_users)} unique users with upcoming insurance dates (from {len(upcoming_users)} total records)")
                
                for user in unique_users:
                    days_until_due = (user.due_day - self.today).days if user.due_day else 0
                    
                    # Determine if we should send a message based on due date or notice date
                    message = None
                    
                    if user.notice == self.today:
                        message = (f"Hello {user.full_name}, this is a reminder that your insurance "
                                  f"for {user.car_type} ({user.license_plate}) will be due on "
                                  f"{format_date(user.due_day)}.")
                    elif user.due_day == self.today:
                        message = (f"Hello {user.full_name}, your insurance for {user.car_type} "
                                  f"({user.license_plate}) is due TODAY. Please make your payment as soon as possible.")
                    
                    if message:
                        # In test mode, send all messages to the test phone number
                        # In production mode, use the user's actual phone number
                        phone_number = TEST_PHONE if self.test_mode else user.cell_phone
                        
                        # Log user details
                        logger.info(f"User: {user.full_name}")
                        logger.info(f"Due: {user.due_day} (in {days_until_due} days)")
                        logger.info(f"Vehicle: {user.car_type} ({user.license_plate})")
                        logger.info(f"Phone: {phone_number if self.test_mode else user.cell_phone}")
                        
                        try:
                            message_id = self.send_message(phone_number, message)
                            if message_id:
                                logger.info(f"Viber message sent successfully. Message ID: {message_id}")
                                messages_sent_count += 1
                        except NotificationError:
                            # Already logged in send_message, just continue with the next user
                            continue
            else:
                logger.info("No users with upcoming insurance dates found.")
            
            return messages_sent_count
        
        except Exception as e:
            logger.error(f"Error checking upcoming insurance: {e}")
            raise NotificationError(f"Error checking upcoming insurance: {e}")