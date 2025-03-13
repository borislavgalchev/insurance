"""
  - Role: Centralized configuration store
  - Contents: Database credentials, Twilio API keys, translation mappings,
  application settings
  - Importance: High - provides configuration for all components

Includes translation mappings for column names and configurable
application behavior settings like notification periods.
"""

import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dotfiles', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info(f"Loaded environment from {dotenv_path}")
else:
    load_dotenv()  # Try default locations
    logger.info("No specific .env file found, using default environment variables")

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'insurance')
}

# Twilio configuration
TWILIO_CONFIG = {
    'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
    'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
    'phone_number': os.getenv('TWILIO_PHONE_NUMBER')
}

# Test phone number for development
TEST_PHONE = os.getenv('TEST_PHONE')

# Date format
DATE_FORMAT = '%d.%m.%Y'

# Column name translations (Bulgarian to English)
BG_to_ENG = {
    'контрагент': 'nickname',
    'име на собственик': 'full_name',
    'телефон': 'cell_phone',
    'авт-ил': 'car_type',
    ' Рег №': 'license_plate',
    ' месец': 'due_month',
    'предупреди на': 'notice',
    'падеж': 'due_day',
    'сключена\n на ': 'made_on',
    'сума': 'amount',
    'вн': 'installments',
    '№ на полица': 'policy_number'
}

# Application settings
DEFAULT_EXCEL_PATH = os.getenv('DEFAULT_EXCEL_PATH')
NOTIFICATION_DAYS_AHEAD = int(os.getenv('NOTIFICATION_DAYS_AHEAD', '5'))
