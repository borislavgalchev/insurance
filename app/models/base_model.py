"""
    - Role: Foundation for all data models
    - Key Functions:
    - from_dict(): Converts dictionaries to model instances
    - to_dict(): Serializes models to dictionaries

Implements type-aware conversion between dictionaries and model objects,
supporting serialization for database storage and deserialization from
database records. Handles type conversion and data validation.
"""
from typing import TypeVar, Dict, Any, Type, cast, Optional, get_type_hints
from datetime import date

T = TypeVar('T', bound='BaseModel')

class BaseModel:
    """
    Base model with common functionality for serialization/deserialization
    """
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary
        
        Args:
            data: Dictionary containing model data
            
        Returns:
            T: A new model instance
        """
        # Handle None case
        if data is None:
            return None
            
        # Use centralized validation based on model type
        if cls.__name__ == 'User':
            from app.utils.validators import validate_user_model
            validated_data = validate_user_model(data)
            return cls(**validated_data)
        
        # Get type hints for this class (for non-User models)
        hints = get_type_hints(cls)
        
        # Create a cleaned data dictionary
        cleaned_data = {}
        
        for field_name, field_type in hints.items():
            # Skip if field is not in data
            if field_name not in data:
                continue
                
            value = data.get(field_name)
            
            # Handle empty strings for Optional fields
            if value == '' and getattr(field_type, '__origin__', None) is Optional:
                cleaned_data[field_name] = None
                continue
                
            # Handle date conversions
            if field_type == Optional[date] or field_type == date:
                if value == '' or value is None:
                    cleaned_data[field_name] = None
                elif isinstance(value, date):
                    cleaned_data[field_name] = value
                else:
                    # Use convert_date from validators
                    from app.utils.validators import convert_date
                    cleaned_data[field_name] = convert_date(value)
                continue
                
            # Handle numeric type conversions
            if field_type == int or getattr(field_type, '__origin__', None) is Optional and field_type.__args__[0] == int:
                if value is None or value == '':
                    cleaned_data[field_name] = 0 if field_type == int else None
                elif isinstance(value, str):
                    try:
                        cleaned_data[field_name] = int(value)
                    except (ValueError, TypeError):
                        cleaned_data[field_name] = 0 if field_type == int else None
                else:
                    cleaned_data[field_name] = value
                continue
                
            # Default case, use value as is
            cleaned_data[field_name] = value
            
        # Create instance
        return cls(**cleaned_data)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            key: getattr(self, key)
            for key in self.__annotations__
            if hasattr(self, key)
        }
