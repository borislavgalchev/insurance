"""
    Role: Command-line interface utilities 

Provides functions for parsing command-line arguments and configuring
application behavior based on user input. Centralizes CLI-related 
functionality to keep the main module focused on orchestration.

Example: 
$py main.py --help
$py main.py --viber
$py main.py --prod
$py main.py --days
$py main.py --excel
"""

import sys
import argparse
from config.settings import DEFAULT_EXCEL_PATH, NOTIFICATION_DAYS_AHEAD


def parse_arguments():
    """
    Parse command line arguments for the Insurance Management System
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Insurance Management System')
    parser.add_argument('--viber', action='store_true', 
                        help='Check upcoming insurance and send Viber messages')
    parser.add_argument('--prod', action='store_true', 
                        help='Run in production mode (send to real numbers)')
    parser.add_argument('--days', type=int, default=NOTIFICATION_DAYS_AHEAD, 
                        help='Number of days ahead to check for due dates')
    parser.add_argument('--excel', type=str, default=DEFAULT_EXCEL_PATH,
                        help='Path to the Excel file')
    
    # For backward compatibility, also check sys.argv and preserve the old --sms flag
    args = parser.parse_args()
    
    # Support both --viber and legacy --sms flag
    args.sms = False  # Initialize flag
    if 'viber' in sys.argv or '--viber' in sys.argv:
        args.sms = True  # We're using sms variable to maintain backward compatibility
    if 'sms' in sys.argv or '--sms' in sys.argv:
        args.sms = True  # Legacy support
    
    if 'prod' in sys.argv or '--prod' in sys.argv:
        args.prod = True
        
    return args