from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel, Field, ValidationError

from orcid2taxid.shared.schemas import InstitutionalAffiliation
from orcid2taxid.researchers.schemas.orcid import (
    OrcidProfile, OrcidAffiliation, OrcidWorks
)
from orcid2taxid.researchers.schemas.base import CustomerProfile
from orcid2taxid.core.logging import get_logger, log_event
from orcid2taxid.researchers.exceptions import OrcidAPIError, OrcidValidationError, OrcidError

logger = get_logger(__name__)

class OrcidConfig(BaseModel):
    """Configuration for ORCID API client"""
    api_key: Optional[str] = None
    timeout: int = Field(default=30, ge=1)
    base_url: str = Field(default="https://pub.orcid.org/v3.0")
    
    @property
    def headers(self) -> Dict[str, str]:
        headers = {'Accept': 'application/vnd.orcid+json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

async def fetch_orcid_data(
    orcid_id: str,
    endpoint: str,
    config: Optional[OrcidConfig] = None
) -> Dict[str, Any]:
    """Generic function to fetch data from ORCID API"""
    if config is None:
        config = OrcidConfig()
        
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            response = await client.get(
                f"{config.base_url}/{orcid_id}/{endpoint}",
                headers=config.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error fetching %s for ORCID %s: %s", endpoint, orcid_id, str(e))
            raise OrcidAPIError(
                f"Failed to fetch {endpoint} data",
                details={
                    "orcid_id": orcid_id,
                    "endpoint": endpoint,
                    "error": str(e)
                }
            ) from e

def parse_affiliations(data: Dict[str, Any]) -> List[InstitutionalAffiliation]:
    """
    Parse education or employment affiliations from ORCID API response.
    Handles the nested structure of ORCID affiliation groups.
    """
    affiliations = []
    for group in data['affiliation-group']:
        for summary in group.get('summaries', []):
            affiliation_data = None
            if 'education-summary' in summary:
                affiliation_data = summary['education-summary']
            elif 'employment-summary' in summary:
                affiliation_data = summary['employment-summary']
            
            if affiliation_data:
                affiliation = OrcidAffiliation.model_validate(affiliation_data)
                affiliations.append(affiliation)
    
    return affiliations

@log_event(__name__)
async def get_profile(orcid_id: str, config: Optional[OrcidConfig] = None) -> CustomerProfile:
    """Fetch and parse researcher metadata from ORCID"""
    try:
        # Fetch all required data
        person_data = await fetch_orcid_data(orcid_id, "person", config)
        works_data = await fetch_orcid_data(orcid_id, "works", config)
        education_data = await fetch_orcid_data(orcid_id, "educations", config)
        employment_data = await fetch_orcid_data(orcid_id, "employments", config)
        
        if not person_data:
            raise OrcidError(
                "No person data found",
                error_code="no_data",
                details={"orcid_id": orcid_id}
            )

        try:
            orcid_profile = OrcidProfile.model_validate(person_data)
            orcid_works = OrcidWorks.model_validate(works_data)
            orcid_educations = parse_affiliations(education_data)
            orcid_employments = parse_affiliations(employment_data)
            
            profile = CustomerProfile.from_orcid_profile(orcid_profile, orcid_id)
            profile.add_educations_from_orcid(orcid_educations)
            profile.add_employments_from_orcid(orcid_employments)
            profile.add_publications_from_orcid(orcid_works)
            
            return profile
            
        except ValidationError as e:
            raise OrcidValidationError(
                "Failed to validate ORCID data",
                validation_error=e,
                details={
                    "orcid_id": orcid_id,
                    "raw_data": {
                        "person": person_data,
                        "works": works_data,
                        "education": education_data,
                        "employment": employment_data
                    }
                }
            ) from e
            
    except Exception as e:
        if not isinstance(e, (OrcidAPIError, OrcidError)):
            logger.error("Error processing author metadata for ORCID %s: %s", orcid_id, str(e))
            raise OrcidAPIError(
                "Failed to process author metadata",
                details={
                    "orcid_id": orcid_id,
                    "error": str(e)
                }
            ) from e
        raise