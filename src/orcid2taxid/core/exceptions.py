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

class IntegrationError(BaseAppError):
    """Base exception for all integration-related errors"""
    def __init__(
        self,
        message: str,
        error_code: str,
        integration: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None
    ):
        self.integration = integration
        super().__init__(
            message=f"{integration} error: {message}",
            error_code=f"{integration}_{error_code}",
            status_code=status_code,
            details=details
        )

# ORCID-specific exceptions
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
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )

class OrcidDataError(OrcidError):
    """Exception for ORCID data parsing/validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="data_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

# Europe PMC-specific exceptions
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
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )

class EpmcDataError(EpmcError):
    """Exception for Europe PMC data parsing/validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="data_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

# LLM-specific exceptions
class LLMError(IntegrationError):
    """Base exception for LLM-related errors"""
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
            integration="llm",
            status_code=status_code,
            details=details
        )

class LLMAPIError(LLMError):
    """Exception for LLM API communication errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="api_error",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )

class LLMParseError(LLMError):
    """Exception for LLM response parsing errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="parse_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        ) 