"""Functions to save sample responses from different API integrations."""

import asyncio
import random
from typing import List, Dict, Any, TypeVar, Generic
from pathlib import Path

from orcid2taxid.researcher.integrations.orcid import (
    get_profile,
    OrcidConfig
)
from orcid2taxid.publication.integrations.epmc import (
    get_epmc_publications_by_orcid,
    EpmcConfig
)
from orcid2taxid.grant.integrations.nih import (
    get_nih_grants_by_pi_name,
    get_nih_grants_by_organization,
    get_nih_grant_by_number,
    NIHConfig
)
from tests.integrations.api_test_cases import (
    SAMPLE_ORCID_IDS,
    SAMPLE_RESEARCHER_NAMES,
    SAMPLE_NIH_RECIPIENT_ORGANIZATIONS,
    SAMPLE_NIH_GRANT_IDS
)
from tests.utils.utils import save_response

T = TypeVar('T')

async def save_orcid_samples(n: int = 2) -> None:
    """Save n sample ORCID profile responses."""
    config = OrcidConfig()
    sample_ids = random.sample(SAMPLE_ORCID_IDS, min(n, len(SAMPLE_ORCID_IDS)))
    
    results = []
    for orcid_id in sample_ids:
        try:
            profile = await get_profile(orcid_id, config)
            results.append({
                "orcid_id": orcid_id,
                "data": profile.model_dump()
            })
        except Exception as e:
            print(f"Error fetching ORCID profile for {orcid_id}: {e}")
    
    # Save up to n random samples
    if results:
        samples = results if len(results) <= n else random.sample(results, n)
        for sample in samples:
            save_response("orcid", f"profile_{sample['orcid_id']}.json", sample["data"])

async def save_epmc_samples(n: int = 2) -> None:
    """
    Save n sample EPMC publication responses.
    
    This function fetches publications for multiple ORCID IDs but saves
    only n publications total, randomly selected from all results.
    """
    config = EpmcConfig()
    all_publications = []
    
    # Collect publications from multiple ORCID IDs
    for orcid_id in SAMPLE_ORCID_IDS:
        try:
            publications = await get_epmc_publications_by_orcid(orcid_id, max_results=10, config=config)
            for pub in publications:
                all_publications.append({
                    "orcid_id": orcid_id,
                    "publication_id": pub.id if hasattr(pub, 'id') else f"pub_{random.randint(1000, 9999)}",
                    "data": pub.model_dump()
                })
        except Exception as e:
            print(f"Error fetching EPMC publications for {orcid_id}: {e}")
    
    # Save up to n random samples
    if all_publications:
        samples = all_publications if len(all_publications) <= n else random.sample(all_publications, n)
        for i, sample in enumerate(samples):
            save_response(
                "epmc", 
                f"publication_{sample['orcid_id']}_{sample['publication_id']}.json", 
                sample["data"]
            )

async def save_nih_samples(n: int = 2) -> None:
    """
    Save n sample NIH grant responses.
    
    This function fetches grants by PI name, organization, and grant number,
    but saves only n grants total, randomly selected from all results.
    """
    config = NIHConfig()
    all_grants = []
    
    # Collect grants from PI names
    for name in SAMPLE_RESEARCHER_NAMES:
        try:
            grants = await get_nih_grants_by_pi_name(name, max_results=5, config=config)
            for grant in grants:
                all_grants.append({
                    "source": f"pi_{name.replace(' ', '_')}",
                    "grant_id": grant.id if hasattr(grant, 'id') else f"grant_{random.randint(1000, 9999)}",
                    "data": grant.model_dump()
                })
        except Exception as e:
            print(f"Error fetching NIH grants for PI {name}: {e}")
    
    # Collect grants from organizations
    for org in SAMPLE_NIH_RECIPIENT_ORGANIZATIONS:
        try:
            grants = await get_nih_grants_by_organization(org, max_results=5, config=config)
            for grant in grants:
                all_grants.append({
                    "source": f"org_{org.replace(' ', '_')}",
                    "grant_id": grant.id if hasattr(grant, 'id') else f"grant_{random.randint(1000, 9999)}",
                    "data": grant.model_dump()
                })
        except Exception as e:
            print(f"Error fetching NIH grants for organization {org}: {e}")
    
    # Collect grants by grant number
    for grant_num in SAMPLE_NIH_GRANT_IDS:
        try:
            grant = await get_nih_grant_by_number(grant_num, config=config)
            if grant:
                all_grants.append({
                    "source": "direct",
                    "grant_id": grant_num,
                    "data": grant.model_dump()
                })
        except Exception as e:
            print(f"Error fetching NIH grant {grant_num}: {e}")
    
    # Save up to n random samples
    if all_grants:
        samples = all_grants if len(all_grants) <= n else random.sample(all_grants, n)
        for sample in samples:
            save_response(
                "nih", 
                f"grant_{sample['source']}_{sample['grant_id']}.json", 
                sample["data"]
            )

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