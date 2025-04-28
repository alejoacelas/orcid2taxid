"""
Common schema classes used across domains.
"""
from .base import (
    EmailInfo,
    ResearcherID,
    ExternalReference,
    ResearcherDescription,
    DatetimeSerializableBaseModel,
    InstitutionalAffiliation,
    ResearcherProfile
)

__all__ = [
    'EmailInfo',
    'ResearcherID',
    'ExternalReference',
    'ResearcherDescription',
    'DatetimeSerializableBaseModel',
    'InstitutionalAffiliation',
    'ResearcherProfile'
]