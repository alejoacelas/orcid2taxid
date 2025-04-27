from typing import Optional, Dict, Any
from fastapi import status
from orcid2taxid.shared.exceptions.base import BaseAppError

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
