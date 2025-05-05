from typing import Any, Dict, Optional
from fastapi import status
from pydantic import ValidationError

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    def __init__(
        self,
        message: str,
        error_code: str = "llm_error",
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

class LLMValidationError(LLMError):
    """Raised when LLM response validation fails."""
    def __init__(
        self,
        message: str,
        validation_error: Optional[ValidationError] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if validation_error:
            details["validation_errors"] = validation_error.errors()
        
        super().__init__(
            message=message,
            error_code="llm_validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class LLMAPIError(LLMError):
    """Raised when there's an error communicating with the LLM API."""
    def __init__(
        self,
        message: str,
        provider: str = "default",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None
    ):
        error_code = f"llm_{provider}_api_error"
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )

class LLMRateLimitError(LLMAPIError):
    """Raised when LLM API rate limits are exceeded."""
    def __init__(
        self,
        message: str = "Rate limit exceeded for LLM API",
        provider: str = "default",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            provider=provider,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        ) 