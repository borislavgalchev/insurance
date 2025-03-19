
import logging
import os
import argparse
from datetime import datetime, timedelta
import pandas as pd

from app.utils.logger import setup_logger

# Set up logging
logger = setup_logger(name=__name__)

from config.settings import BG_to_ENG

from app.services.excel_service import ExcelService
from app.utils.exceptions import DataImportError

def read_excel_file(file_path):
    """
    Read data from Excel file and translate column headers from Bulgarian to English.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        pd.DataFrame: DataFrame with translated column headers
    """
    try:
        logger.info(f"Reading Excel file: {file_path}")
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # Use ExcelService to read and translate the file
        excel_service = ExcelService(file_path)
        return excel_service.df
        
    except DataImportError as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading Excel file: {str(e)}")
        return None

from app.utils.date_helpers import parse_date

def process_data(df):
    """
    Process the data by extracting required fields, converting date formats,
    and filtering out invalid entries.
    
    Args:
        df (pd.DataFrame): DataFrame with raw data
        
    Returns:
        pd.DataFrame: Processed DataFrame with required fields
    """
    # Check if DataFrame is empty or None
    if df is None or df.empty:
        logger.error("Empty or invalid DataFrame provided")
        return None
    
    # Verify required columns are present
    required_columns = ['full_name', 'cell_phone', 'notice', 'due_day']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns: {', '.join(missing_columns)}")
        return None
    
    # Create a new DataFrame with only the required columns
    processed_df = df[required_columns].copy()
    
    # Remove rows with missing values in required fields
    initial_row_count = len(processed_df)
    processed_df = processed_df.dropna(subset=['full_name', 'cell_phone'])
    
    if len(processed_df) < initial_row_count:
        logger.info(f"Removed {initial_row_count - len(processed_df)} rows with missing name or phone")
    
    # Parse date columns using the utility function
    try:
        # Apply parse_date to each date column
        for date_col in ['notice', 'due_day']:
            processed_df[date_col] = processed_df[date_col].apply(parse_date)
            
            # Count and report None values
            none_count = processed_df[date_col].isna().sum()
            if none_count > 0:
                logger.warning(f"Found {none_count} invalid date values in {date_col}")
        
        # Drop rows with invalid dates
        processed_df = processed_df.dropna(subset=['notice', 'due_day'])
        logger.info(f"Final processed dataset has {len(processed_df)} valid entries")
        
        # Sort by due_day and notice date
        processed_df = processed_df.sort_values(by=['due_day', 'notice'])
        
        return processed_df
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return None

from app.utils.date_helpers import get_upcoming_dates, format_date
from app.utils.display import show_notification_mode, show_sms_count
from app.services.notification_service import NotificationService

def deduplicate_users(users):
    """
    Deduplicate users based on name and due date
    
    Args:
        users: List of user objects or dictionaries
        
    Returns:
        List of unique users
    """
    seen = set()
    unique_users = []
    
    for user in users:
        # Create a unique key based on name and due date
        if hasattr(user, 'full_name') and hasattr(user, 'due_day'):
            # For User objects
            key = (user.full_name, str(user.due_day))
        else:
            # For dictionaries
            key = (user['full_name'], str(user.get('due_date', '')))
        
        if key not in seen:
            seen.add(key)
            unique_users.append(user)
            
    return unique_users

def generate_notifications(df):
    """
    Generate notifications based on due dates and notice preferences.
    
    Notifications are generated if:
    1. due_date is today, or
    2. notice date is exactly 5 days from today
    
    Args:
        df (pd.DataFrame): Processed DataFrame
        
    Returns:
        list: List of notification messages
    """
    notifications = []
    # These variables will be global for testing purposes
    global today, five_days_ahead
    if not 'today' in globals():
        today = datetime.now().date()
        five_days_ahead = get_upcoming_dates(today, 5)
    
    logger.info(f"Generating notifications for today ({today}) and 5-day notices ({five_days_ahead})")
    
    # Check if DataFrame is empty or None
    if df is None or df.empty:
        logger.warning("No data available for generating notifications")
        return notifications
    
    # Create a notification service instance for phone number normalization
    notification_service = NotificationService(None, test_mode=True)
    
    # Process due date notifications (due date is today)
    due_today = df[df['due_day'] == today]
    for _, row in due_today.iterrows():
        # Normalize phone number for display
        phone = row['cell_phone']
        phone_display = notification_service.normalize_phone(phone) if phone else "NO PHONE"
        if not phone_display:
            phone_display = "NO PHONE"
            
        notification = {
            'type': 'due_today',
            'full_name': row['full_name'],
            'cell_phone': row['cell_phone'],
            'message': f"URGENT: Payment is due TODAY for {row['full_name']} ({phone_display})"
        }
        notifications.append(notification)
    
    # Process notice date notifications (notice date is 5 days from now)
    notice_match = df[df['notice'] == five_days_ahead]
    for _, row in notice_match.iterrows():
        # Normalize phone number for display
        phone = row['cell_phone']
        phone_display = notification_service.normalize_phone(phone) if phone else "NO PHONE"
        if not phone_display:
            phone_display = "NO PHONE"
            
        notification = {
            'type': 'upcoming_notice',
            'full_name': row['full_name'],
            'cell_phone': row['cell_phone'],
            'due_date': format_date(row['due_day']),
            'message': f"REMINDER: Upcoming payment for {row['full_name']} ({phone_display}) on {format_date(row['due_day'])}"
        }
        notifications.append(notification)
    
    logger.info(f"Generated {len(notifications)} notifications")
    return notifications

def format_for_viber(notification):
    """
    Format notification for Viber chatbot integration.
    
    Args:
        notification (dict): Notification data
        
    Returns:
        dict: Viber-formatted message
    """
    # Create a notification service instance for phone number normalization
    notification_service = NotificationService(None, test_mode=True)
    
    # Normalize the phone number
    phone = notification['cell_phone']
    normalized_phone = notification_service.normalize_phone(phone)
    
    # If phone is invalid, use 'UNKNOWN'
    if not normalized_phone:
        normalized_phone = 'UNKNOWN'
    
    # Use the format_viber_message method from our NotificationService
    # Create a mock user object with the phone number
    from app.models.user import User
    mock_user = User(
        nickname="",
        full_name=notification['full_name'],
        cell_phone=phone,
        car_type="",
        license_plate=""
    )
        
    return notification_service.format_viber_message(mock_user, notification['message'])

from app.utils.cli import parse_arguments

def main():
    """Main function to process Excel file and generate notifications."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process Excel file for notifications')
    parser.add_argument('file_path', help='Path to the Excel file')
    parser.add_argument('--viber', action='store_true', help='Format output for Viber integration')
    parser.add_argument('--test-date', help='Override today\'s date for testing (YYYY-MM-DD format)')
    args = parser.parse_args()
    
    # Override today's date if specified (useful for testing)
    global today, five_days_ahead
    if args.test_date:
        try:
            today = datetime.strptime(args.test_date, '%Y-%m-%d').date()
            five_days_ahead = get_upcoming_dates(today, 5)
            logger.info(f"Overriding today's date to: {today} for testing")
        except ValueError:
            logger.error(f"Invalid date format: {args.test_date}. Using current date.")
            today = datetime.now().date()
            five_days_ahead = get_upcoming_dates(today, 5)
    
    # Read and process Excel file
    df = read_excel_file(args.file_path)
    if df is None:
        logger.error("Failed to read Excel file. Exiting.")
        return
    
    # Process data
    processed_df = process_data(df)
    if processed_df is None:
        logger.error("Failed to process data. Exiting.")
        return
        
    # Print overview of processed data
    min_date = min(processed_df['due_day']) if not processed_df['due_day'].empty else None
    max_date = max(processed_df['due_day']) if not processed_df['due_day'].empty else None
    logger.info(f"Processing complete. Data contains records from {min_date} to {max_date}")
    
    # Generate notifications
    notifications = generate_notifications(processed_df)
    
    # Output results
    if not notifications:
        print("No notifications to send today.")
    else:
        print(f"Found {len(notifications)} notifications:")
        
        if args.viber:
            # Format for Viber integration
            viber_messages = [format_for_viber(notification) for notification in notifications]
            
            # Here you would integrate with the Viber API
            # For demonstration, we just print the formatted messages
            for message in viber_messages:
                print(f"Viber message to {message['receiver']}: {message['text']}")
        else:
            # Regular console output with better formatting
            print("\n===== NOTIFICATIONS =====")
            
            # Group notifications by type
            due_today_notifications = [n for n in notifications if n['type'] == 'due_today']
            upcoming_notifications = [n for n in notifications if n['type'] == 'upcoming_notice']
            
            if due_today_notifications:
                print("\n🔴 DUE TODAY:")
                for notification in due_today_notifications:
                    print(f"- {notification['message']}")
                    
            if upcoming_notifications:
                print("\n🔔 UPCOMING REMINDERS:")
                for notification in upcoming_notifications:
                    print(f"- {notification['message']}")
                    
            print("\n=========================")
            
        # Show total count
        show_sms_count(len(notifications))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        raise

