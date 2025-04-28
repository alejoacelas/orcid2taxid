"""Functions to save sample responses from different API integrations."""

import asyncio
import random
from typing import TypeVar

from orcid2taxid.researcher.integrations.orcid import fetch_orcid_data
from orcid2taxid.publication.integrations.epmc import fetch_epmc_data
from orcid2taxid.grant.integrations.nih import fetch_nih_data
from tests.api_test_cases import (
    SAMPLE_ORCID_IDS,
    SAMPLE_NIH_GRANT_IDS,
    SAMPLE_EPMC_ORCID_IDS,
)
from tests.utils.utils import save_response

T = TypeVar('T')

async def save_orcid_samples(n: int = 2) -> None:
    """Save n sample ORCID profile responses."""
    sample_ids = random.sample(SAMPLE_ORCID_IDS, min(n, len(SAMPLE_ORCID_IDS)))
    
    for orcid_id in sample_ids:
        # Fetch raw data for person, works, educations, and employments
        person_data = await fetch_orcid_data(orcid_id, "person")
        works_data = await fetch_orcid_data(orcid_id, "works")
        education_data = await fetch_orcid_data(orcid_id, "educations")
        employment_data = await fetch_orcid_data(orcid_id, "employments")
        
        # Save each raw response separately
        save_response("samples_researcher_orcid", f"person_{orcid_id}.json", person_data)
        save_response("samples_researcher_orcid", f"works_{orcid_id}.json", works_data)
        save_response("samples_researcher_orcid", f"educations_{orcid_id}.json", education_data)
        save_response("samples_researcher_orcid", f"employments_{orcid_id}.json", employment_data)

async def save_epmc_samples(n: int = 2) -> None:
    """
    Save n sample EPMC publication responses.
    
    This function fetches publications for multiple ORCID IDs and saves
    the raw API responses.
    """
    counter = 0
    
    # Collect publications from multiple ORCID IDs
    for orcid_id in SAMPLE_EPMC_ORCID_IDS:
        if counter >= n:
            break
            
        # Construct query parameters for ORCID search
        payload = {
            'query': f'AUTHORID:"{orcid_id}"',
            'resultType': 'core',
            'pageSize': 10,
            'format': 'json'
        }
        
        # Fetch raw data from EPMC
        raw_data = await fetch_epmc_data(payload=payload)
        
        # Save raw response
        save_response("samples_publication_epmc", f"publications_{orcid_id}.json", raw_data)
        counter += 1

async def save_nih_samples(n: int = 2) -> None:
    """
    Save n sample NIH grant responses.
    
    This function fetches grants by PI name, organization, and grant number,
    and saves the raw API responses.
    """
    counter = 0
        
    # Save grants by grant number
    for grant_num in SAMPLE_NIH_GRANT_IDS:
        if counter >= n:
            break
            
        # Construct search payload
        payload = {
            "criteria": {
                "project_nums": [grant_num]
            },
            "limit": 1,
            "offset": 0
        }
        
        # Fetch raw data
        raw_data = await fetch_nih_data(payload=payload)
        
        # Save raw response
        save_response("samples_grant_nih", f"grant_{grant_num}.json", raw_data)
        counter += 1

async def save_all_samples(n: int = 2) -> None:
    """
    Save n samples from all API integrations.
    
    The parameter n controls the number of samples to save from each integration,
    not the total number of samples.
    """
    await asyncio.gather(
        save_orcid_samples(n),
        save_epmc_samples(n),
        save_nih_samples(n)
    )

if __name__ == "__main__":
    asyncio.run(save_all_samples())