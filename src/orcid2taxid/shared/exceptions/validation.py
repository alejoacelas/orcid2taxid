from typing import Optional, Dict, Any, List
from pydantic import ValidationError
from fastapi import status
from orcid2taxid.shared.exceptions.integration import IntegrationError

class ValidationErrorMixin:
    """Mixin to handle Pydantic validation errors with detailed field information"""
    def __init__(
        self,
        message: str,
        validation_error: ValidationError,
        error_code: str,
        integration: str,
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
        details: Optional[Dict[str, Any]] = None
    ):
        # Extract detailed validation errors
        validation_details = self._format_validation_errors(validation_error)
        
        # Merge with any additional details
        merged_details = {
            "validation_errors": validation_details,
            **(details or {})
        }
        
        # Call IntegrationError's __init__ directly
        IntegrationError.__init__(
            self,
            message=message,
            error_code=error_code,
            integration=integration,
            status_code=status_code,
            details=merged_details
        )
    
    def _format_validation_errors(self, validation_error: ValidationError) -> List[Dict[str, Any]]:
        """Format Pydantic validation errors into a structured format"""
        formatted_errors = []
        for error in validation_error.errors():
            # Get the field path as a string
            field_path = " -> ".join(str(x) for x in error["loc"])
            
            # Get the model class name if available
            model_name = None
            if len(error["loc"]) > 0:
                try:
                    model_name = error["loc"][0].__class__.__name__
                except (AttributeError, IndexError):
                    pass
            
            formatted_errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error["input"],
                "model": model_name
            })
        return formatted_errors

class DataValidationError(IntegrationError, ValidationErrorMixin):
    """Base class for all data validation errors"""
    def __init__(
        self,
        message: str,
        validation_error: ValidationError,
        integration: str,
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
        details: Optional[Dict[str, Any]] = None
    ):
        ValidationErrorMixin.__init__(
            self,
            message=message,
            validation_error=validation_error,
            error_code="validation_error",
            integration=integration,
            status_code=status_code,
            details=details
        )