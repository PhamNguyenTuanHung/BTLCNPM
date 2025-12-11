"""
Utility functions for date/time formatting and conversion
"""
from datetime import datetime

def format_datetime_display(dt):
    """
    Chuyển đổi DATETIME từ DB sang format hiển thị dd/mm/yyyy HH:MM:SS
    
    Args:
        dt: datetime object hoặc None
        
    Returns:
        String format dd/mm/yyyy HH:MM:SS hoặc empty string
    """
    if dt is None:
        return ''
    if isinstance(dt, datetime):
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    return str(dt)


def format_date_display(dt):
    """
    Chuyển đổi DATE từ DB sang format hiển thị dd/mm/yyyy (chỉ ngày)
    
    Args:
        dt: datetime object hoặc None
        
    Returns:
        String format dd/mm/yyyy hoặc empty string
    """
    if dt is None:
        return ''
    if isinstance(dt, datetime):
        return dt.strftime('%d/%m/%Y')
    return str(dt)


def parse_date_input(date_str, default=None):
    """
    Parse date string từ user input (dd/mm/yyyy) sang datetime object
    
    Args:
        date_str: String format dd/mm/yyyy
        default: Giá trị mặc định nếu parse fail
        
    Returns:
        datetime object hoặc default value
    """
    if not date_str:
        return default
    
    try:
        # Try dd/mm/yyyy format
        return datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        try:
            # Try yyyy-mm-dd format (ISO)
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return default


def parse_datetime_input(datetime_str, default=None):
    """
    Parse datetime string từ user input sang datetime object
    
    Args:
        datetime_str: String format dd/mm/yyyy HH:MM:SS hoặc dd/mm/yyyy
        default: Giá trị mặc định nếu parse fail
        
    Returns:
        datetime object hoặc default value
    """
    if not datetime_str:
        return default
    
    try:
        # Try dd/mm/yyyy HH:MM:SS format
        return datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
    except ValueError:
        try:
            # Try dd/mm/yyyy format (set time to 00:00:00)
            return datetime.strptime(datetime_str, '%d/%m/%Y')
        except ValueError:
            try:
                # Try ISO format
                return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return default
