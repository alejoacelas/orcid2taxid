"""
Common exception classes used across domains.
"""

from .base import BaseAppError
from .validation import ValidationError, DataValidationError
from .integration import IntegrationError

__all__ = [
    'BaseAppError', 'ValidationError', 'DataValidationError', 'IntegrationError'
] 