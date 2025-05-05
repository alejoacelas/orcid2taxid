"""
Organisms domain package - handling taxonomic information and NCBI taxonomy integration.
"""

from orcid2taxid.organism.schemas.ncbi import NCBITaxonomyInfo
from orcid2taxid.organism.schemas.base import OrganismMention
from orcid2taxid.organism.integrations.ncbi import (
    get_taxonomy_info,
    fetch_taxid_search,
    fetch_taxonomy_record,
    NCBIConfig
)
from orcid2taxid.organism.exceptions import (
    OrganismError,
    NCBIAPIError,
    NCBIValidationError,
    OrganismNotFoundError
)

__all__ = [
    # Models
    "NCBITaxonomyInfo",
    "OrganismMention",
    
    # Functions
    "get_taxonomy_info",
    "fetch_taxid_search",
    "fetch_taxonomy_record",
    
    # Config
    "NCBIConfig",
    
    # Exceptions
    "OrganismError",
    "NCBIAPIError",
    "NCBIValidationError",
    "OrganismNotFoundError"
] 