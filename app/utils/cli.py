"""
    Role: Command-line interface utilities 

Provides functions for parsing command-line arguments and configuring
application behavior based on user input. Centralizes CLI-related 
functionality to keep the main module focused on orchestration.

Example: 
$py main.py --help
$py main.py --sms
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
    parser.add_argument('--sms', action='store_true', 
                        help='Check upcoming insurance and send SMS')
    parser.add_argument('--prod', action='store_true', 
                        help='Run in production mode (send to real numbers)')
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
