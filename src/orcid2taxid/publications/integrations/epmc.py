from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel, Field, ValidationError
from orcid2taxid.publications.schemas.base import PublicationRecord
from orcid2taxid.publications.schemas.epmc import EpmcResponse
from orcid2taxid.core.logging import get_logger, log_event
from orcid2taxid.publications.exceptions import EpmcAPIError, EpmcValidationError

logger = get_logger(__name__)

class EpmcConfig(BaseModel):
    """Configuration for Europe PMC API client"""
    timeout: int = Field(default=30, ge=1)
    base_url: str = Field(default="https://www.ebi.ac.uk/europepmc/webservices/rest")
    
    @property
    def headers(self) -> Dict[str, str]:
        return {'Accept': 'application/json'}

async def fetch_epmc_data(
    endpoint: str,
    params: Dict[str, Any],
    config: Optional[EpmcConfig] = None
) -> Dict[str, Any]:
    """Generic function to fetch data from Europe PMC API"""
    if config is None:
        config = EpmcConfig()
        
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            response = await client.get(
                f"{config.base_url}/{endpoint}",
                params=params,
                headers=config.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error fetching %s from Europe PMC: %s", endpoint, str(e))
            raise EpmcAPIError(
                f"Failed to fetch {endpoint} data",
                details={
                    "endpoint": endpoint,
                    "params": params,
                    "error": str(e)
                }
            ) from e

def parse_publication(data: Dict[str, Any]) -> List[PublicationRecord]:
    """
    Parse publication data from Europe PMC API response.
    Converts raw API response into a list of PublicationRecord objects.
    """
    try:
        epmc_response = EpmcResponse.model_validate(data)
        return PublicationRecord.from_epmc_response(epmc_response)
    except ValidationError as e:
        raise EpmcValidationError(
            "Failed to validate Europe PMC publication data",
            validation_error=e,
            details={
                "raw_data": data  # Include the raw data for debugging
            }
        ) from e

@log_event(__name__)
async def get_publications_by_orcid(
    orcid_id: str,
    max_results: int = 20,
    config: Optional[EpmcConfig] = None
) -> List[PublicationRecord]:
    """Fetch and parse publications from Europe PMC using ORCID ID"""
    try:
        # Construct query parameters for ORCID search
        params = {
            'query': f'AUTHORID:"{orcid_id}"',
            'resultType': 'core',
            'pageSize': max_results,
            'format': 'json'
        }
        
        # Fetch data from EPMC
        data = await fetch_epmc_data('search', params, config)
        # Parse and return publications
        return parse_publication(data)
        
    except Exception as e:
        if not isinstance(e, (EpmcAPIError, EpmcValidationError)):
            logger.error("Error processing publications for ORCID %s: %s", orcid_id, str(e))
            raise EpmcAPIError(
                "Failed to process publications",
                details={
                    "orcid_id": orcid_id,
                    "error": str(e)
                }
            ) from e
        raise