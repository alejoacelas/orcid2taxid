"""Utility functions for date handling and conversion."""
from datetime import datetime, date
from typing import Optional, Union, Dict

def parse_date_to_iso(date_value: Union[str, datetime, date, Dict, None]) -> Optional[str]:
    """
    Parse various date formats to ISO format string (YYYY-MM-DD).
    
    Args:
        date_value: Date value that could be:
            - ISO format string
            - datetime/date object
            - Dictionary with year/month/day components
            - None
            
    Returns:
        ISO format string (YYYY-MM-DD) or None if parsing fails
    """
    if not date_value:
        return None
        
    try:
        # If already a string, try to parse and reformat
        if isinstance(date_value, str):
            return datetime.strptime(date_value, "%Y-%m-%d").date().isoformat()
            
        # If datetime or date object, convert to ISO string
        if isinstance(date_value, (datetime, date)):
            return date_value.isoformat()
            
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
                # Create ISO format date string
                return f"{year}-{month:0>2}-{day:0>2}"
                
        return None
        
    except (ValueError, TypeError, AttributeError):
        return None 