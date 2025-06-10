from typing import List

from orcid2taxid.grant.schemas import GrantRecord
from orcid2taxid.grant.integrations.nih import get_nih_grant_by_number, get_nih_grants_by_pi_name
from orcid2taxid.shared.schemas import ResearcherProfile

def _is_nih_grant(funder: str) -> bool:
    """Check if a grant is from NIH"""
    nih_keywords = {'nih', 'national institutes of health', 'national institute of health'}
    return any(keyword in funder.lower() for keyword in nih_keywords)

async def _enhance_grant_metadata(grant: GrantRecord) -> GrantRecord:
    """Enhance grant metadata using NIH APIs if applicable"""
    if not grant.id:
        return grant
    
    # Try to enhance with NIH data if it's an NIH grant
    if _is_nih_grant(grant.funder or ''):
        try:
            nih_grant = await get_nih_grant_by_number(grant.id)
            if nih_grant:
                return nih_grant
        except Exception as e:
            # Log the error but don't let it crash the app
            # Return the original grant if NIH enhancement fails
            from orcid2taxid.core.logging import get_logger
            logger = get_logger(__name__)
            logger.warning("Failed to enhance grant %s with NIH data: %s", grant.id, str(e))
            return grant
    return grant

async def find_grants(researcher: ResearcherProfile, max_results: int = 20) -> ResearcherProfile:
    """Fetch and add grants to researcher metadata"""
    # Get grants from publications - using a list instead of a set to avoid hash errors
    publication_grants: List[GrantRecord] = []
    for publication in researcher.publications:
        for grant in publication.grants:  # Using grants instead of funding_info
            # Enhance grant metadata if it's from NIH
            enhanced_grant = await _enhance_grant_metadata(grant)
            if enhanced_grant not in publication_grants:
                publication_grants.append(enhanced_grant)
    
    # Get grants from NIH Reporter by PI name
    researcher_name = f"{researcher.researcher_id.given_name} {researcher.researcher_id.family_name}"
    nih_grants = await get_nih_grants_by_pi_name(researcher_name, max_results)
    
    # Combine all grants
    all_grants = publication_grants + nih_grants
    
    # Remove duplicates based on project number
    unique_grants = {}
    for grant in all_grants:
        if grant.id:  # Using id instead of project_num based on GrantRecord schema
            unique_grants[grant.id] = grant
        elif grant.title:  # Using title instead of project_title based on GrantRecord schema
            unique_grants[grant.title] = grant
    
    # Update researcher with unique grants
    researcher.grants = list(unique_grants.values())
    
    return researcher 