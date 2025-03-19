# Insurance Management System

A system for managing insurance customer data, tracking due dates, and sending Viber notifications for upcoming payments.

## Project Structure

```
/insurance/
├── config/
│   └── settings.py  # All configurations + env vars for credentials
├── app/
│   ├── models/
│   │   ├── base_model.py  # Base model with common functionality
│   │   └── user.py  # User data model
│   ├── repositories/
│   │   └── user_repository.py  # Data access layer
│   ├── services/
│   │   ├── database.py  # Database connection management
│   │   ├── excel_service.py  # Excel data import
│   │   ├── insurance_service.py  # Core business logic
│   │   └── notification_service.py  # Viber notifications
│   └── utils/
│       ├── cli.py  # Command-line interface utilities
│       ├── date_helpers.py  # Date-related utilities
│       ├── decorators.py  # Common decorators for logging and error handling
│       ├── exceptions.py  # Custom exceptions
│       ├── logger.py  # Centralized logging configuration
│       ├── repository.py  # Base repository with common CRUD operations
│       └── validators.py  # Validation utilities
├── tests/
│   └── test_phone.py # Tests for valid phone numbers
└── main.py  # Application entry point
```

## Features

- Import insurance data from Excel files
- Store customer data in a MySQL database
- Track insurance due dates
- Send Viber notifications for upcoming payments
- View customers with approaching or overdue payments

## Requirements

- mysql-connector-python>=8.0.0
- pandas>=1.3.0
- viberbot>=1.0.12
- python-dotenv>=0.19.0

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install mysql-connector-python pandas viberbot python-dotenv
   ```
3. Set up environment variables in `.env` file:

   ```
   DB_HOST=localhost
   DB_USER=insurance_user
   DB_PASSWORD=your_password
   DB_NAME=insurance

   VIBER_AUTH_TOKEN=your_viber_auth_token
   VIBER_BOT_NAME=Insurance Notifications
   VIBER_AVATAR_URL=https://example.com/bot-avatar.jpg
   VIBER_WEBHOOK_URL=https://your-webhook-url.com/viber/webhook
   TEST_PHONE=your_test_phone

   DEFAULT_EXCEL_PATH=path/to/excel/file.xlsx
   NOTIFICATION_DAYS_AHEAD=5
   ```

## Viber Bot Setup

To use Viber for notifications, you'll need to:

1. Create a Viber Bot through the [Viber Developer Console](https://developers.viber.com/)
2. Obtain your authentication token and add it to the `.env` file
3. Set up a webhook URL to receive events (optional for one-way messaging)
4. Optionally provide an avatar URL for your bot

## Usage

Run the application with the following command:

```
python main.py
```

### Command Line Arguments

- `--viber`: Check upcoming insurance and send Viber notifications
- `--prod`: Run in production mode (send to real phone numbers)
- `--days`: Number of days ahead to check for due dates (default is 5)
- `--excel`: Path to the Excel file (default is specified in settings)

Example:

```
python main.py --viber --days 7
```

## Development

### Project Architecture

- **Domain Layer**: Models representing business entities
- **Data Access Layer**: Repositories for database operations
- **Service Layer**: Business logic implementation
- **Utility Layer**: Helper functions and tools
- **Configuration**: Environment-specific settings

### Key Components

1. **Base Model**: Common serialization/deserialization for all models
2. **User Model**: Represents an insurance customer
3. **Base Repository**: Common CRUD operations for all repositories
4. **Database Service**: Manages database connections with error handling
5. **User Repository**: Handles user data access
6. **Excel Service**: Imports data from Excel files
7. **Insurance Service**: Core business logic
8. **Notification Service**: Sends Viber notifications
9. **Decorators**: Common logging and error handling
10. **Date Helpers**: Date manipulation utilities
11. **Validators**: Validation functions and utilities
12. **Logger**: Centralized logging configuration

### Code Organization

The project uses several design patterns:

1. **Repository Pattern**: Abstracts data access logic
2. **Service Layer**: Encapsulates business logic
3. **Decorator Pattern**: For cross-cutting concerns like logging and error handling
4. **Base Class Inheritance**: For shared functionality in models and repositories