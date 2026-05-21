"""
Numeric Utilities for UTAS Simulation

Provides robust numeric extraction functions that can handle various response formats
from LLMs, including descriptive text mixed with numbers.
"""

import re
from typing import Union, Optional


def extract_numeric_value(value: Union[str, int, float], default: int = 3, min_val: int = 1, max_val: int = 5) -> int:
    """
    Extracts a numeric value from various input formats, with fallback to default.
    
    Handles:
    - Pure integers/floats
    - Descriptive strings with numbers (e.g., "moderate (3)", "3 (high intensity)")
    - Text descriptions that map to numeric values
    - Invalid inputs (returns default)
    
    Args:
        value: Input value to extract number from
        default: Default value if extraction fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Integer value clamped between min_val and max_val
    """
    if isinstance(value, (int, float)):
        return max(min_val, min(int(value), max_val))
    
    if not isinstance(value, str):
        return default
    
    value_str = str(value).lower().strip()
    
    number_match = re.search(r'\b(\d+)\b', value_str)
    if number_match:
        try:
            num = int(number_match.group(1))
            return max(min_val, min(num, max_val))
        except ValueError:
            pass
    
    descriptive_mapping = {
        'very low': 1, 'minimal': 1, 'trivial': 1, 'easy': 1,
        'low': 2, 'simple': 2, 'basic': 2,
        'moderate': 3, 'medium': 3, 'average': 3, 'normal': 3,
        'high': 4, 'difficult': 4, 'challenging': 4, 'hard': 4,
        'very high': 5, 'extreme': 5, 'maximum': 5, 'intense': 5, 'severe': 5,
        
        'light': 2, 'moderate': 3, 'heavy': 4, 'intense': 5,
        
        'effortless': 1, 'routine': 2, 'standard': 3, 'demanding': 4, 'grueling': 5
    }
    
    for term, num in descriptive_mapping.items():
        if term in value_str:
            return max(min_val, min(num, max_val))
    
    try:
        num = float(value_str)
        return max(min_val, min(int(round(num)), max_val))
    except ValueError:
        pass
    
    return default


def safe_int_conversion(value: Union[str, int, float], field_name: str = "value", default: int = 0) -> int:
    """
    Safely converts a value to integer with descriptive error handling.
    
    Args:
        value: Value to convert
        field_name: Name of the field for error messages
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        if isinstance(value, (int, float)):
            return int(value)
        
        if isinstance(value, str):
            number_match = re.search(r'-?\d+(?:\.\d+)?', str(value))
            if number_match:
                return int(float(number_match.group()))
        
        print(f"Warning: Could not convert {field_name} '{value}' to integer, using default {default}")
        return default
        
    except (ValueError, TypeError) as e:
        print(f"Warning: Error converting {field_name} '{value}' to integer: {e}, using default {default}")
        return default
