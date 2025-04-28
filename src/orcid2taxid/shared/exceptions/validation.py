from typing import Optional, Dict, Any
from pydantic import ValidationError
from fastapi import status

class ValidationErrorMixin:
    """Mixin that provides validation error string representation"""
    def __init__(self, validation_error: ValidationError):
        self.validation_error = validation_error
        
    def format_validation_errors(self) -> str:
        """Format validation errors into a readable string"""
        validation_details = self.validation_error.errors()
        
        if not validation_details:
            return str(self.__cause__)
            
        # Format each validation error into a readable string
        formatted_errors = []
        for error in validation_details:
            loc = ".".join(str(p) for p in error.get("loc", []))
            msg = error.get("msg", "")
            input_val = error.get("input")
            formatted_errors.append(
                f"Field '{loc}': {msg}\n"
                f"{'='*80}\n"
                f"Input: {input_val}\n"
                f"{'='*80}\n"
            )
        
        return "\n".join(formatted_errors)

class DataValidationError(Exception):
    """Class for handling data validation errors with detailed field information"""
    def __init__(
        self,
        message: str,
        validation_error: ValidationError,
        integration: str,
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.integration = integration
        self.status_code = status_code
        self.details = {
            "validation_errors": validation_error.errors(),
            **(details or {})
        }
        self._validation_mixin = ValidationErrorMixin(validation_error)
        super().__init__(self.message)
        
    def __str__(self):
        """Custom string representation to include detailed error information"""
        return f"{self.message}\n{self._validation_mixin.format_validation_errors()}"