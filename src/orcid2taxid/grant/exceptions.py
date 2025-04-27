from typing import Any, Dict, Optional

class NIHAPIError(Exception):
    """Base exception for NIH Reporter API errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class NIHValidationError(NIHAPIError):
    """Exception raised when NIH Reporter data validation fails"""
    def __init__(self, message: str, validation_error: Exception, details: Optional[Dict[str, Any]] = None):
        self.validation_error = validation_error
        super().__init__(message, details)

class NIHError(NIHAPIError):
    """Generic NIH Reporter error"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        super().__init__(message, details) 