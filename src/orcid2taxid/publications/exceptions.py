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

class EpmcValidationError(DataValidationError):
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
        
    def __str__(self):
        # Get the original ValidationError
        original_error = self.__cause__
        error_details = []
        
        # Process validation errors from the parent class
        if hasattr(self, 'details') and self.details and 'validation_errors' in self.details:
            for error in self.details['validation_errors']:
                field = error.get('field', 'unknown field')
                msg = error.get('message', 'unknown error')
                input_val = error.get('input')
                error_details.append(f"Field '{field}': {msg} (received: {input_val!r})")
        
        # Get contextual information from the details
        context_info = ""
        if hasattr(self, 'details') and self.details:
            # Extract useful fields from raw data if available
            if 'raw_data' in self.details:
                raw_data = self.details['raw_data']
                # Add identifier information if available
                if isinstance(raw_data, dict):
                    if 'resultList' in raw_data and 'result' in raw_data['resultList']:
                        results = raw_data['resultList']['result']
                        if results and len(results) > 0:
                            result = results[0]
                            if 'doi' in result and result['doi']:
                                context_info += f"\nDOI: {result['doi']}"
                            if 'title' in result and result['title']:
                                context_info += f"\nTitle: {result['title'][:50]}..." if len(result['title']) > 50 else f"\nTitle: {result['title']}"
                            if 'authorString' in result and result['authorString']:
                                context_info += f"\nAuthors: {result['authorString'][:50]}..." if len(result['authorString']) > 50 else f"\nAuthors: {result['authorString']}"
                            if 'authorList' in result and result['authorList']:
                                authors = result['authorList']['author']
                                for author in authors:
                                    context_info += f"\nAuthor: {author['firstName']}, {author['lastName']}"
        
        # Combine validation errors with context info
        detailed_message = "\n".join(error_details) if error_details else str(original_error)
        return f"{self.message}\n{detailed_message}{context_info}"
