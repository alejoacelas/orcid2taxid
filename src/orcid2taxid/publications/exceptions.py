from typing import Optional, Dict, Any
from pydantic import ValidationError
from fastapi import status
from orcid2taxid.shared.exceptions import IntegrationError, DataValidationError

class EpmcError(IntegrationError):
    """Base exception for Europe PMC API errors"""
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
            integration="epmc",
            status_code=status_code,
            details=details
        )

class EpmcAPIError(EpmcError):
    """Exception for Europe PMC API communication errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="api_error",
            details=details
        )

class EpmcDataError(DataValidationError):
    """Exception for Europe PMC data parsing/validation errors"""
    def __init__(
        self,
        message: str,
        validation_error: ValidationError,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            validation_error=validation_error,
            integration="epmc",
            details=details
        )
