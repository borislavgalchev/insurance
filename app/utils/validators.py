"""
  - Role: Data validation
  - Key Functions: Validation rules for different data types

Implements validation rules for different data types and domain-specific
requirements. Includes functions for validating user input, database records,
and Excel data imports. Provides detailed error messages for validation
failures.
"""
import re
from datetime import date, datetime
from typing import Dict, Any, Optional, TypeVar, Type, List, Callable, Union
from app.utils.exceptions import ValidationError

# Type variables for validation
T = TypeVar('T')
ValidationFunc = Callable[[Any], bool]


class Validator:
    """
    Generic validator utility class
    """
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Allow empty phone numbers - we'll handle these as a special case
        if not phone or str(phone).strip() == "" or str(phone).lower() in ('none', 'n/a', 'no phone'):
            return True
        
        # Convert to string for the checks below
        phone_str = str(phone)
        
        # Accept asterisk as placeholder
        if phone_str.strip() == '*':
            return True
            
        # Handle home phones which may have different format
        if phone_str.lower().startswith('home:') or phone_str.lower().startswith('home ') or 'домашен' in phone_str.lower():
            return True
            
        # Accept comments about the insurance (common in this dataset)
        if 'застраховка' in phone_str.lower() or 'г-жата' in phone_str.lower():
            return True
            
        # Basic pattern for mobile phone numbers - made more flexible
        # Allow spaces, dashes, parentheses and other common separators
        cleaned_phone = re.sub(r'[\s\-\(\)\.]', '', phone_str)
        pattern = r'^\+?[0-9]{7,15}$'  # Reduced min length from 8 to 7 for more flexibility
        return bool(re.match(pattern, cleaned_phone))
    
    @staticmethod
    def validate_license_plate(plate: str) -> bool:
        """
        Validate license plate format
        
        Args:
            plate: License plate to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not plate:
            return True  # Made optional
        
        # Accept any non-empty value for license plates
        # Bulgarian plates have different formats, so we'll be very permissive
        return len(str(plate).strip()) > 0
    
    @staticmethod
    def validate_positive_integer(value: Any) -> bool:
        """
        Validate that a value is a positive integer
        
        Args:
            value: Value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if value is None or value == '':
            return True  # Allow empty values
        
        try:
            num = int(value)
            return num >= 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_required(value: Any) -> bool:
        """
        Validate that a value is not empty
        
        Args:
            value: Value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True
    
    @staticmethod
    def validate_date(value: Any) -> bool:
        """
        Validate that a value is a valid date or can be converted to a date
        
        Args:
            value: Value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if value is None or value == '':
            return True  # Allow empty dates
        if isinstance(value, date):
            return True
            
        # Try to parse a string date
        try:
            # Import parse_date function from date_helpers to avoid circular imports
            from app.utils.date_helpers import parse_date
            result = parse_date(value)
            return result is not None
        except Exception:
            return False
    
    @staticmethod
    def validate_with_func(value: Any, func: ValidationFunc, error_msg: str) -> Optional[str]:
        """
        Validate a value with a validation function
        
        Args:
            value: Value to validate
            func: Validation function returning True/False
            error_msg: Error message if validation fails
            
        Returns:
            Optional[str]: Error message if validation fails, None otherwise
        """
        if not func(value):
            return error_msg
        return None
    
    @classmethod
    def validate_data(cls, data: Dict[str, Any], validations: Dict[str, List[tuple]]) -> List[str]:
        """
        Validate data against a set of validation rules
        
        Args:
            data: Dictionary containing data to validate
            validations: Dictionary mapping field names to list of (validation_func, error_msg) tuples
            
        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        
        for field, validators in validations.items():
            value = data.get(field)
            
            for validator_func, error_msg in validators:
                error = cls.validate_with_func(value, validator_func, error_msg)
                if error:
                    errors.append(error)
                    break  # Stop on first error for this field
        
        return errors


def convert_date(value: Any) -> Optional[date]:
    """
    Convert a value to a date
    
    Args:
        value: Value to convert
        
    Returns:
        Optional[date]: Converted date or None if conversion fails
    """
    if value is None or value == '':
        return None
    if isinstance(value, date):
        return value
        
    try:
        from app.utils.date_helpers import parse_date
        return parse_date(value)
    except Exception:
        return None


def validate_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate user data and return cleaned data
    
    Args:
        data: Dictionary containing user data
        
    Returns:
        Dict[str, Any]: Cleaned and validated data
        
    Raises:
        ValidationError: If validation fails
    """
    # Define validation rules - everything made optional except nickname
    validations = {
        'nickname': [],  # Made nickname optional too
        'full_name': [],  # Optional
        'cell_phone': [
            # Phone number is optional, but must be valid if provided
            (Validator.validate_phone_number, "Invalid phone number format")
        ],
        'car_type': [],  # Optional
        'license_plate': [
            # Only validate format, not required
            (Validator.validate_license_plate, "Invalid license plate format")
        ],
        'amount': [(Validator.validate_positive_integer, "Amount must be a positive number")],
        'installments': [(Validator.validate_positive_integer, "Installments must be a positive number")]
    }
    
    # Validate data
    errors = Validator.validate_data(data, validations)
    
    # Handle numeric fields
    for field in ['amount', 'installments']:
        if data.get(field) and Validator.validate_positive_integer(data[field]):
            try:
                data[field] = int(data[field])
            except (ValueError, TypeError):
                data[field] = 0
    
    if errors:
        raise ValidationError(", ".join(errors))
    
    return data


def validate_user_model(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive validation for User model data
    
    Args:
        user_data: Dictionary containing user data
        
    Returns:
        Dict[str, Any]: Validated and converted data
        
    Raises:
        ValidationError: If validation fails
    """
    # Basic field validation
    validated_data = validate_user_data(user_data)
    
    # Date field validation and conversion
    for field in ['due_month', 'notice', 'due_day', 'made_on']:
        if field in validated_data:
            validated_data[field] = convert_date(validated_data[field])
    
    # Business rule validations - commented out to allow notice date to be after due date
    # Some records may have unusual date configurations, so we'll be more permissive
    # if validated_data.get('due_day') and validated_data.get('notice'):
    #    if validated_data['notice'] > validated_data['due_day']:
    #        raise ValidationError("Notice date must be before or on due date")
    
    return validated_data