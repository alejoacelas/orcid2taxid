from typing import Dict, Any, Optional
from pydantic import ValidationError

class OrganismError(Exception):
    """Base exception for all organism-related errors"""
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

class NCBIAPIError(OrganismError):
    """Raised when there's an error communicating with the NCBI API"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code="ncbi_api_error",
            details=details
        )

class NCBIValidationError(OrganismError):
    """Raised when NCBI data fails validation"""
    def __init__(
        self,
        message: str,
        validation_error: ValidationError,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["validation_errors"] = validation_error.errors()
        super().__init__(
            message,
            error_code="ncbi_validation_error",
            details=details
        )

class OrganismNotFoundError(OrganismError):
    """Raised when an organism cannot be found"""
    def __init__(
        self, 
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code="organism_not_found",
            details=details
        ) 