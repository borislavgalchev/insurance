"""
Validation utilities for the Insurance Management System
"""
import re
from datetime import date
from typing import Dict, Any, Optional, TypeVar, Type, List, Callable
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
        if not phone:
            return False
            
        # Basic pattern for phone numbers
        pattern = r'^\+?[0-9]{8,15}$'
        return bool(re.match(pattern, phone.strip()))
    
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
            return False
            
        # Adjust pattern based on your country's license plate format
        pattern = r'^[A-Z0-9]{2,10}$'
        return bool(re.match(pattern, plate.strip()))
    
    @staticmethod
    def validate_positive_integer(value: Any) -> bool:
        """
        Validate that a value is a positive integer
        
        Args:
            value: Value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
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
    # Define validation rules
    validations = {
        'nickname': [(Validator.validate_required, "Nickname is required")],
        'full_name': [(Validator.validate_required, "Full name is required")],
        'cell_phone': [
            (Validator.validate_required, "Cell phone is required"),
            (Validator.validate_phone_number, "Invalid phone number format")
        ],
        'car_type': [(Validator.validate_required, "Car type is required")],
        'license_plate': [
            (Validator.validate_required, "License plate is required"),
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
            data[field] = int(data[field])
    
    if errors:
        raise ValidationError(", ".join(errors))
    
    return data