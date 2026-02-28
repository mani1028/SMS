"""
Input validation utilities for API requests
"""

import re
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Custom validation error"""
    pass


class InputValidator:
    """Centralized input validation"""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that all required fields are present in data.
        
        Args:
            data: Request data dictionary
            required_fields: List of required field names
            
        Raises:
            ValidationError: If any required field is missing or empty
        """
        if not data:
            raise ValidationError("Request body is required")
        
        for field in required_fields:
            if field not in data or data[field] is None or str(data[field]).strip() == "":
                raise ValidationError(f"Field '{field}' is required")
    
    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format"""
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            raise ValidationError(f"Invalid email format: {email}")
    
    @staticmethod
    def validate_string(value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> None:
        """Validate string length and format"""
        if not isinstance(value, str):
            raise ValidationError(f"Field '{field_name}' must be a string")
        
        value = str(value).strip()
        if len(value) < min_length or len(value) > max_length:
            raise ValidationError(
                f"Field '{field_name}' must be between {min_length} and {max_length} characters"
            )
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Validate integer value and range"""
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Field '{field_name}' must be an integer")
        
        if min_val is not None and int_val < min_val:
            raise ValidationError(f"Field '{field_name}' must be at least {min_val}")
        
        if max_val is not None and int_val > max_val:
            raise ValidationError(f"Field '{field_name}' must be at most {max_val}")
        
        return int_val
    
    @staticmethod
    def validate_boolean(value: Any, field_name: str) -> bool:
        """Validate boolean value"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes'):
                return True
            elif value.lower() in ('false', '0', 'no'):
                return False
        
        raise ValidationError(f"Field '{field_name}' must be a boolean")
    
    @staticmethod
    def validate_phone(phone: str) -> None:
        """Validate phone number format (basic)"""
        if not phone or not re.match(r'^[\d\s\-\+\(\)]+$', phone) or len(phone.replace(' ', '').replace('-', '').replace('+', '').replace('(', '').replace(')', '')) < 10:
            raise ValidationError(f"Invalid phone number: {phone}")
    
    @staticmethod
    def validate_admission_no(admission_no: str) -> None:
        """Validate admission number format"""
        if not admission_no or len(admission_no.strip()) < 2:
            raise ValidationError("Admission number must be at least 2 characters")
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input by stripping whitespace and removing dangerous chars"""
        if not isinstance(value, str):
            return str(value)
        return value.strip()


# Validation schemas for common endpoints
STUDENT_CREATE_SCHEMA = {
    'name': {'type': 'string', 'required': True, 'min': 2, 'max': 255},
    'admission_no': {'type': 'string', 'required': False, 'min': 2, 'max': 100},  # Auto-generated if not provided
    'class_name': {'type': 'string', 'required': True, 'min': 1, 'max': 50},
    'section': {'type': 'string', 'required': False, 'max': 20},
    'roll_no': {'type': 'string', 'required': False, 'max': 50},
    'email': {'type': 'email', 'required': False},
    'phone': {'type': 'phone', 'required': False},
    'gender': {'type': 'string', 'required': False, 'max': 20},
    'dob': {'type': 'string', 'required': False},  # Format: YYYY-MM-DD
    'blood_group': {'type': 'string', 'required': False, 'max': 10},
    'address': {'type': 'string', 'required': False},
    'previous_school': {'type': 'string', 'required': False, 'max': 255},
    'admission_date': {'type': 'string', 'required': False},  # Format: YYYY-MM-DD
    'parent_name': {'type': 'string', 'required': False, 'max': 255},
    'parent_phone': {'type': 'phone', 'required': False},
    'parent_email': {'type': 'email', 'required': False},
}

STUDENT_UPDATE_SCHEMA = {
    'name': {'type': 'string', 'required': False, 'min': 2, 'max': 255},
    'class_name': {'type': 'string', 'required': False, 'min': 1, 'max': 50},
    'section': {'type': 'string', 'required': False, 'max': 20},
    'roll_no': {'type': 'string', 'required': False, 'max': 50},
    'email': {'type': 'email', 'required': False},
    'phone': {'type': 'phone', 'required': False},
    'gender': {'type': 'string', 'required': False, 'max': 20},
    'dob': {'type': 'string', 'required': False},
    'blood_group': {'type': 'string', 'required': False, 'max': 10},
    'address': {'type': 'string', 'required': False},
    'previous_school': {'type': 'string', 'required': False, 'max': 255},
    'admission_date': {'type': 'string', 'required': False},
    'status': {'type': 'string', 'required': False},
    'is_active': {'type': 'boolean', 'required': False},
    'parent_name': {'type': 'string', 'required': False, 'max': 255},
    'parent_phone': {'type': 'phone', 'required': False},
    'parent_email': {'type': 'email', 'required': False},
}

SCHOOL_REGISTER_SCHEMA = {
    'school_name': {'type': 'string', 'required': True, 'min': 2, 'max': 255},
    'school_email': {'type': 'email', 'required': True},
    'admin_name': {'type': 'string', 'required': True, 'min': 2, 'max': 255},
    'admin_email': {'type': 'email', 'required': True},
    'admin_password': {'type': 'string', 'required': True, 'min': 8},
}

LOGIN_SCHEMA = {
    'email': {'type': 'email', 'required': True},
    'password': {'type': 'string', 'required': True, 'min': 1},
    'school_id': {'type': 'integer', 'required': True, 'min': 1},
}


def validate_schema(data: Dict[str, Any], schema: Dict) -> None:
    """
    Validate data against a schema.
    
    Args:
        data: Data to validate
        schema: Schema dict with field definitions
        
    Raises:
        ValidationError: If validation fails
    """
    for field, rules in schema.items():
        required = rules.get('required', False)
        field_type = rules.get('type', 'string')
        
        if field not in data or data[field] is None:
            if required:
                raise ValidationError(f"Field '{field}' is required")
            continue
        
        value = data[field]
        
        if field_type == 'string':
            InputValidator.validate_string(
                value, 
                field,
                min_length=rules.get('min', 1),
                max_length=rules.get('max', 255)
            )
        
        elif field_type == 'email':
            InputValidator.validate_email(value)
        
        elif field_type == 'integer':
            InputValidator.validate_integer(
                value,
                field,
                min_val=rules.get('min'),
                max_val=rules.get('max')
            )
        
        elif field_type == 'boolean':
            InputValidator.validate_boolean(value, field)
        
        elif field_type == 'phone':
            InputValidator.validate_phone(value)
