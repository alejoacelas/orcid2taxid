from typing import Optional, Dict, Any
from fastapi import status

class BaseAppError(Exception):
    """Base exception for all application errors"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }
