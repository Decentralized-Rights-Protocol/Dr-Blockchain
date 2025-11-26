"""Time utility functions."""

from datetime import datetime, timezone
from typing import Optional


def get_timestamp() -> float:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).timestamp()


def format_datetime(dt: Optional[datetime] = None) -> str:
    """
    Format datetime as ISO string.
    
    Args:
        dt: Datetime object (defaults to now)
        
    Returns:
        ISO formatted string
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()


def parse_datetime(iso_string: str) -> datetime:
    """
    Parse ISO datetime string.
    
    Args:
        iso_string: ISO formatted datetime string
        
    Returns:
        Datetime object
    """
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))

