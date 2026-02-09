"""
Utility functions for converting query parameters to proper types.
Handles conversion of string values like "1"/"0" or "true"/"false" to boolean.
"""
from typing import Optional, Union


def str_to_bool(value: Optional[Union[str, bool, int]]) -> bool:
    """
    Convert string/numeric query parameter to boolean.
    Handles: "1", "0", "true", "false", "True", "False", 1, 0, True, False, None
    
    Args:
        value: Query parameter value (can be string, bool, int, or None)
    
    Returns:
        bool: True for "1"/"true"/1/True, False for "0"/"false"/0/False/None
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        value_lower = value.strip().lower()
        if value_lower in ("1", "true", "yes", "on"):
            return True
        if value_lower in ("0", "false", "no", "off", ""):
            return False
        # If it's not a recognized boolean string, default to False
        return False
    return False
