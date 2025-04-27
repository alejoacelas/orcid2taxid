"""
Schemas for researcher profiles and related data.
"""

from .base import CustomerProfile
from .orcid import (
    OrcidProfile, OrcidAffiliation, OrcidWorks
)

__all__ = [
    'CustomerProfile', 'OrcidProfile', 'OrcidAffiliation', 'OrcidWorks'
] 