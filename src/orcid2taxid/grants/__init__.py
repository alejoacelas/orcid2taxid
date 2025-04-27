"""
Grants domain package - handling grant information from NIH and NSF.
"""

# Re-export schemas
from .schemas import GrantSchema, GrantMetadata

# Re-export services
from .services import extract_grants, merge_grants

# Re-export integrations
from .integrations import search_nih_grants, search_nsf_grants

__all__ = [
    'GrantSchema', 'GrantMetadata',
    'extract_grants', 'merge_grants',
    'search_nih_grants', 'search_nsf_grants'
] 