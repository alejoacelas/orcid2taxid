from typing import List, Dict, Optional, Any
import httpx
from pydantic import BaseModel, Field, ValidationError

from orcid2taxid.grant.schemas.base import GrantRecord
from orcid2taxid.grant.schemas.nih import NIHSearchResponse
from orcid2taxid.grant.exceptions import NIHAPIError, NIHValidationError, NIHError
from orcid2taxid.core.logging import get_logger, log_event

logger = get_logger(__name__)

class NIHConfig(BaseModel):
    """Configuration for NIH Reporter API client"""
    api_key: Optional[str] = None
    timeout: int = Field(default=30, ge=1)
    base_url: str = Field(default="https://api.reporter.nih.gov/v2")
    
    @property
    def headers(self) -> dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

async def fetch_nih_data(
    payload: Dict[str, Any],
    endpoint: str = 'projects/search',
    config: Optional[NIHConfig] = None
) -> Dict[str, Any]:
    """Generic function to fetch data from NIH Reporter API"""
    if config is None:
        config = NIHConfig()
        
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            response = await client.post(
                f"{config.base_url}/{endpoint}",
                headers=config.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error fetching %s from NIH Reporter: %s", endpoint, str(e))
            raise NIHAPIError(
                f"Failed to fetch {endpoint} data",
                details={
                    "endpoint": endpoint,
                    "error": str(e)
                }
            ) from e

@log_event(__name__)
async def get_nih_grants_by_pi_name(
    pi_name: str,
    max_results: int = 20,
    config: Optional[NIHConfig] = None
) -> List[GrantRecord]:
    """Search NIH Reporter by PI name and convert results to GrantRecord objects"""
    try:
        # Construct search payload
        payload = {
            "criteria": {
                "pi_names": [{"any_name": pi_name}],
                "advanced_text_search": {
                    "operator": "AND",
                    "search_field": "all",
                    "search_text": pi_name
                }
            },
            "limit": max_results,
            "offset": 0,
            "sort_field": "project_start_date",
            "sort_order": "desc"
        }
        
        # Fetch data
        raw_data = await fetch_nih_data(payload=payload, config=config)
        if not raw_data:
            return []
        
        # Parse response
        try:
            response = NIHSearchResponse.model_validate(raw_data)
        except ValidationError as e:
            raise NIHValidationError(
                "Failed to validate NIH Reporter response",
                validation_error=e,
                details={"raw_data": raw_data}
            ) from e
        
        # Convert results to GrantRecord objects
        grant_list = []
        for project in response.results:
            try:
                grant = GrantRecord.from_nih_project(project)
                grant_list.append(grant)
            except NIHValidationError as e:
                logger.warning("Skipping invalid project: %s", str(e))
                continue
        
        return grant_list
        
    except Exception as e:
        if not isinstance(e, (NIHAPIError, NIHError)):
            logger.error("Error searching NIH Reporter by PI name: %s", str(e))
            raise NIHAPIError(
                "Failed to search NIH Reporter by PI name",
                details={
                    "pi_name": pi_name,
                    "error": str(e)
                }
            ) from e
        raise

@log_event(__name__)
async def get_nih_grants_by_organization(
    org_name: str,
    max_results: int = 20,
    config: Optional[NIHConfig] = None
) -> List[GrantRecord]:
    """Search NIH Reporter by organization name and convert results to GrantRecord objects"""
    try:
        # Construct search payload
        payload = {
            "criteria": {
                "org_names": [org_name],
                "advanced_text_search": {
                    "operator": "AND",
                    "search_field": "all",
                    "search_text": org_name
                }
            },
            "limit": max_results,
            "offset": 0,
            "sort_field": "project_start_date",
            "sort_order": "desc"
        }
        
        # Fetch data
        raw_data = await fetch_nih_data(payload=payload, config=config)
        if not raw_data:
            return []
        
        # Parse response
        try:
            response = NIHSearchResponse.model_validate(raw_data)
        except ValidationError as e:
            raise NIHValidationError(
                "Failed to validate NIH Reporter response",
                validation_error=e,
                details={"raw_data": raw_data}
            ) from e
        
        # Convert results to GrantRecord objects
        grant_list = []
        for project in response.results:
            try:
                grant = GrantRecord.from_nih_project(project)
                grant_list.append(grant)
            except NIHValidationError as e:
                logger.warning("Skipping invalid project: %s", str(e))
                continue
        
        return grant_list
        
    except Exception as e:
        if not isinstance(e, (NIHAPIError, NIHError)):
            logger.error("Error searching NIH Reporter by organization: %s", str(e))
            raise NIHAPIError(
                "Failed to search NIH Reporter by organization",
                details={
                    "org_name": org_name,
                    "error": str(e)
                }
            ) from e
        raise

@log_event(__name__)
async def get_nih_grant_by_number(
    project_number: str,
    config: Optional[NIHConfig] = None
) -> Optional[GrantRecord]:
    """Get a single grant by its project number from NIH Reporter"""
    try:
        # Construct search payload
        payload = {
            "criteria": {
                "project_nums": [project_number]
            },
            "limit": 1,
            "offset": 0
        }
        
        # Fetch data
        raw_data = await fetch_nih_data(payload=payload, config=config)
        if not raw_data:
            logger.warning("No grant found for project number: %s", project_number)
            return None
        
        # Parse response
        try:
            response = NIHSearchResponse.model_validate(raw_data)
        except ValidationError as e:
            raise NIHValidationError(
                "Failed to validate NIH Reporter response",
                validation_error=e,
                details={"raw_data": raw_data}
            ) from e
        
        # Get the first result and convert it to GrantRecord
        if not response.results:
            logger.warning("No grant found for project number: %s", project_number)
            return None
            
        return GrantRecord.from_nih_project(response.results[0])
        
    except Exception as e:
        if not isinstance(e, (NIHAPIError, NIHError)):
            logger.error("Error getting grant by project number: %s", str(e))
            raise NIHAPIError(
                "Failed to get grant by project number",
                details={
                    "project_number": project_number,
                    "error": str(e)
                }
            ) from e
        raise
