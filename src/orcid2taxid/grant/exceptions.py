from typing import Any, Dict, Optional
from fastapi import status
from pydantic import ValidationError
from orcid2taxid.shared.exceptions.integration import IntegrationError
from orcid2taxid.shared.exceptions.validation import ValidationErrorMixin

class NIHError(IntegrationError):
    """Base exception for NIH Reporter API errors"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            integration="nih",
            status_code=status_code,
            details=details
        )

class NIHAPIError(NIHError):
    """Exception for NIH Reporter API communication errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="api_error",
            details=details
        )

class NIHValidationError(NIHError):
    """Exception raised when NIH Reporter data validation fails"""
    def __init__(
        self,
        message: str,
        validation_error: ValidationError,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )
        self._validation_mixin = ValidationErrorMixin(validation_error)
        
    def __str__(self):
        """Custom string representation to include detailed error information"""
        return f"{self.message}\n{self._validation_mixin.format_validation_errors()}" 