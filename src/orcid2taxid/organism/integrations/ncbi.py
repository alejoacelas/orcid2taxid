import os
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

from orcid2taxid.organism.schemas.ncbi import (
    NCBITaxonomyInfo,
    NCBISearchResult,
    NCBITaxonomyResponse
)
from orcid2taxid.organism.exceptions import (
    NCBIAPIError,
    NCBIValidationError,
    OrganismNotFoundError
)
from orcid2taxid.core.logging import get_logger, log_event
from orcid2taxid.llm.schemas.organism_mention import OrganismMention
from orcid2taxid.organism.schemas.base import OrganismMentionWithTaxid

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class NCBIConfig(BaseModel):
    """Configuration for NCBI API client"""
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("NCBI_API_KEY"))
    timeout: int = Field(default=30, ge=1)
    base_url: str = Field(default="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
    tool_name: str = Field(default="orcid2taxid")
    
    @property
    def params(self) -> Dict[str, str]:
        params = {'tool': self.tool_name}
        if self.api_key:
            params['api_key'] = self.api_key
        return params

async def fetch_ncbi_data(
    endpoint: str,
    params: Dict[str, Any],
    config: Optional[NCBIConfig] = None
) -> Dict[str, Any]:
    """Generic function to fetch data from NCBI API"""
    if config is None:
        config = NCBIConfig()
    
    # Merge default params with provided params
    request_params = {**config.params, **params}
    
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            url = f"{config.base_url}/{endpoint}.fcgi"
            response = await client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Error fetching %s with params %s: %s", endpoint, params, str(e))
            raise NCBIAPIError(
                f"Failed to fetch {endpoint} data",
                details={
                    "endpoint": endpoint,
                    "params": params,
                    "error": str(e)
                }
            ) from e
        except httpx.RequestError as e:
            logger.error("Error fetching %s with params %s: %s", endpoint, params, str(e))
            raise NCBIAPIError(
                f"Failed to fetch {endpoint} data",
                details={
                    "error": str(e)
                }
            ) from e

@log_event(__name__)
async def fetch_taxid_search(
    organism_name: str,
    config: Optional[NCBIConfig] = None
) -> NCBISearchResult:
    """
    Search for taxonomy IDs using organism name
    
    :param organism_name: The name of the organism to search for
    :param config: Optional API configuration
    :return: Search result with taxonomy IDs
    :raises: NCBIAPIError, NCBIValidationError
    """
    if not organism_name:
        raise ValueError("Organism name cannot be empty")
    
    try:
        # Search for taxonomy IDs
        search_params = {
            'db': 'taxonomy',
            'term': organism_name.strip(),
            'retmode': 'json'
        }
        
        search_data = await fetch_ncbi_data('esearch', search_params, config)
        logger.debug("Search response: %s", search_data)
        
        try:
            search_result = NCBISearchResult.model_validate(search_data)
            
            # Check if we got any results
            if not search_result.id_list:
                logger.warning("No results found for organism: %s", organism_name)
                raise OrganismNotFoundError(
                    message=f"No taxonomy records found for '{organism_name}'",
                    details={"organism_name": organism_name}
                )
                
            return search_result
            
        except ValidationError as e:
            raise NCBIValidationError(
                "Failed to validate NCBI search response",
                validation_error=e,
                details={
                    "organism_name": organism_name,
                    "raw_data": search_data
                }
            ) from e
            
    except Exception as e:
        if not isinstance(e, (NCBIAPIError, OrganismNotFoundError)):
            logger.error("Error searching NCBI taxonomy for %s: %s", organism_name, str(e))
            raise NCBIAPIError(
                "Failed to search NCBI taxonomy",
                details={
                    "organism_name": organism_name,
                    "error": str(e)
                }
            ) from e
        raise

@log_event(__name__)
async def fetch_taxonomy_record(
    taxid: str,
    config: Optional[NCBIConfig] = None
) -> NCBITaxonomyResponse:
    """
    Fetch taxonomy record by ID
    
    :param taxid: Taxonomy ID to fetch
    :param config: Optional API configuration
    :return: Taxonomy record
    :raises: NCBIAPIError, NCBIValidationError
    """
    try:
        # Fetch taxonomy record
        fetch_params = {
            'db': 'taxonomy',
            'id': taxid,
            'retmode': 'json'
        }
        
        fetch_data = await fetch_ncbi_data('esummary', fetch_params, config)
        
        try:
            return NCBITaxonomyResponse.model_validate(fetch_data)
            
        except ValidationError as e:
            raise NCBIValidationError(
                "Failed to validate NCBI taxonomy response",
                validation_error=e,
                details={
                    "taxid": taxid,
                    "raw_data": fetch_data
                }
            ) from e
            
    except Exception as e:
        if not isinstance(e, (NCBIAPIError, NCBIValidationError)):
            logger.error("Error fetching NCBI taxonomy record for %s: %s", taxid, str(e))
            raise NCBIAPIError(
                "Failed to fetch NCBI taxonomy record",
                details={
                    "taxid": taxid,
                    "error": str(e)
                }
            ) from e
        raise

@log_event(__name__)
async def get_taxonomy_info(
    organism_mention: OrganismMention,
    config: Optional[NCBIConfig] = None
) -> OrganismMentionWithTaxid:
    """
    Get comprehensive taxonomy information for an organism
    
    :param organism_mention: OrganismMention object containing the organism information
    :param config: Optional API configuration
    :return: OrganismMentionWithTaxid object with taxonomy details
    :raises: NCBIAPIError, NCBIValidationError, OrganismNotFoundError
    """
    if not organism_mention.name:
        raise ValueError("Organism name cannot be empty")
    
    try:
        # First search for the taxonomy ID
        search_result = await fetch_taxid_search(organism_mention.name, config)
        
        # Get the first (most relevant) taxonomy ID
        taxid = search_result.id_list[0]
        
        # Fetch the full taxonomy record
        taxonomy_response = await fetch_taxonomy_record(taxid, config)
        
        if not taxonomy_response.uids:
            raise OrganismNotFoundError(
                message=f"No taxonomy record found for ID '{taxid}'",
                details={
                    "organism_name": organism_mention.name,
                    "taxid": taxid
                }
            )
        
        # Get the first record
        tax_record = taxonomy_response.result.get(taxid)
        if not tax_record:
            raise OrganismNotFoundError(
                message=f"No taxonomy record found for ID '{taxid}'",
                details={
                    "organism_name": organism_mention.name,
                    "taxid": taxid
                }
            )
        
        # Create NCBITaxonomyInfo object
        taxonomy_info = NCBITaxonomyInfo.model_validate(tax_record.model_dump())
        
        # Convert to OrganismMentionWithTaxid
        return OrganismMentionWithTaxid.from_taxonomy_info(organism_mention, taxonomy_info)
        
    except Exception as e:
        if not isinstance(e, (NCBIAPIError, NCBIValidationError, OrganismNotFoundError)):
            logger.error("Error getting taxonomy info for %s: %s", organism_mention.name, str(e))
            raise NCBIAPIError(
                "Failed to get taxonomy info",
                details={
                    "organism_name": organism_mention.name,
                    "error": str(e)
                }
            ) from e
        raise