"""Utility functions for date handling and conversion."""
from datetime import datetime, date
from typing import Optional, Union, Dict

def parse_date(date_value: Union[str, datetime, date, Dict, None]) -> Optional[datetime]:
    """
    Parse various date formats to datetime object.
    
    Args:
        date_value: Date value that could be:
            - ISO format string
            - datetime/date object
            - Dictionary with year/month/day components
            - None
            
    Returns:
        datetime object or None if parsing fails
    """
    if not date_value:
        return None
        
    try:
        # If already a string, try to parse
        if isinstance(date_value, str):
            return datetime.strptime(date_value, "%Y-%m-%d")
            
        # If datetime object, return as is
        if isinstance(date_value, datetime):
            return date_value
            
        # If date object, convert to datetime
        if isinstance(date_value, date):
            return datetime.combine(date_value, datetime.min.time())
            
        # If dictionary with date components
        if isinstance(date_value, dict):
            # Get year, month, day values handling nested dicts
            def get_value(field):
                field_data = date_value.get(field, {})
                if isinstance(field_data, dict):
                    return field_data.get('value')
                return field_data
                
            year = get_value('year')
            # Default to 01 for month/day if not provided
            month = get_value('month') or '01'
            day = get_value('day') or '01'
            
            if year:
                # Create datetime object
                return datetime(int(year), int(month), int(day))
                
        return None
        
    except (ValueError, TypeError, AttributeError):
        return None


def ensure_datetime(date_value: Union[datetime, date, None]) -> Optional[datetime]:
    """
    Ensure a date value is a datetime object.
    
    Args:
        date_value: A datetime, date, or None value
        
    Returns:
        datetime object or None
    """
    if date_value is None:
        return None
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time())
    return None 