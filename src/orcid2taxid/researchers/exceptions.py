from typing import Optional, Dict, Any
from pydantic import ValidationError
from fastapi import status
from orcid2taxid.shared.exceptions.integration import IntegrationError
from orcid2taxid.shared.exceptions.validation import DataValidationError

class OrcidError(IntegrationError):
    """Base exception for ORCID API errors"""
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
            integration="orcid",
            status_code=status_code,
            details=details
        )

class OrcidAPIError(OrcidError):
    """Exception for ORCID API communication errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="api_error",
            details=details
        )

class OrcidValidationError(DataValidationError):
    """Exception for ORCID data parsing/validation errors"""
    def __init__(
        self,
        message: str,
        validation_error: ValidationError,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            validation_error=validation_error,
            integration="orcid",
            details=details
        )
