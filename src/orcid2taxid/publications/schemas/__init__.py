"""
Schemas for publications and related data.
"""

from .base import PublicationRecord
from .epmc import EpmcResponse

__all__ = [
    'PublicationRecord',
    'EpmcResponse'
]
