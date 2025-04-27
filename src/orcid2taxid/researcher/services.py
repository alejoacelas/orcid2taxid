from typing import List, Optional
from orcid2taxid.shared.schemas import (
    ResearcherProfile,
    ExternalReference
)
from orcid2taxid.publication.schemas import PublicationRecord
from orcid2taxid.publication.integrations.epmc import get_epmc_publications_by_orcid as get_epmc_publications
from orcid2taxid.researcher.integrations.orcid import get_profile
from orcid2taxid.core.logging import log_event, get_logger

logger = get_logger(__name__)

@log_event(__name__)
async def get_researcher_by_orcid(orcid_id: str) -> ResearcherProfile:
    """
    Get researcher metadata from ORCID ID
    
    Args:
        orcid_id: The ORCID identifier for the researcher
        
    Returns:
        ResearcherProfile: Complete researcher profile with metadata
    """
    profile = await get_profile(orcid_id)
    return profile

@log_event(__name__)
async def find_publications(
    researcher: ResearcherProfile, 
    max_results: Optional[int] = None
) -> ResearcherProfile:
    """
    Fetch and add publications to researcher metadata
    
    Args:
        researcher: The researcher profile to enrich
        max_results: Maximum number of publications to fetch
        
    Returns:
        ResearcherProfile: The enriched researcher profile
    """
    # Get publications from Europe PMC source
    epmc_papers = await get_epmc_publications(researcher.orcid, max_results)
    
    # Get publications from ORCID (already in the profile)
    orcid_papers = researcher.publications if hasattr(researcher, 'publications') else []
    
    # Deduplicate and update researcher
    unique_papers = _deduplicate_publications(epmc_papers + orcid_papers)
    if max_results is not None:
        unique_papers = unique_papers[:max_results]
    
    researcher.publications = unique_papers
    
    # Enrich researcher metadata from publications
    _enrich_from_publications(researcher)
    return researcher

def _deduplicate_publications(publications: List[PublicationRecord]) -> List[PublicationRecord]:
    """
    Deduplicate publications based on DOI
    
    Args:
        publications: List of publications to deduplicate
        
    Returns:
        List[PublicationRecord]: Deduplicated list of publications
    """
    seen_dois = set()
    unique_pubs = []
    
    for paper in publications:
        if paper.doi and paper.doi in seen_dois:
            continue
        if paper.doi:
            seen_dois.add(paper.doi)
        unique_pubs.append(paper)
    
    return unique_pubs

def _find_matching_author(
    researcher: ResearcherProfile, 
    authors: List[ResearcherProfile]
) -> Optional[ResearcherProfile]:
    """
    Find the author entry that matches this researcher
    
    Args:
        researcher: The researcher to match
        authors: List of authors to search through
        
    Returns:
        Optional[ResearcherProfile]: Matching author if found
    """
    for author in authors:
        # Match by ORCID if available
        if author.orcid and author.orcid == researcher.orcid:
            return author
        
        # Match by email if available
        if (author.email and researcher.email and 
            author.email.address == researcher.email.address):
            return author
        
        # Match by name if available
        if author.full_name and author.full_name == researcher.full_name:
            return author
        
        # Match by given/family name if available
        if (author.given_name and author.family_name and 
            researcher.given_name and researcher.family_name and
            author.given_name == researcher.given_name and 
            author.family_name == researcher.family_name):
            return author
    
    return None

def _enrich_from_publications(researcher: ResearcherProfile) -> None:
    """
    Enrich researcher metadata from publications
    
    Args:
        researcher: The researcher profile to enrich
    """
    # Ensure fields exist before trying to update them
    if not hasattr(researcher, 'alternative_names'):
        researcher.alternative_names = set()
    if not hasattr(researcher, 'keywords'):
        researcher.keywords = set()
    if not hasattr(researcher, 'subjects'):
        researcher.subjects = set()
    if not hasattr(researcher, 'journals'):
        researcher.journals = set()
    if not hasattr(researcher, 'external_ids'):
        researcher.external_ids = {}
    if not hasattr(researcher, 'grants'):
        researcher.grants = []
        
    for paper in researcher.publications:
        author = _find_matching_author(researcher, paper.authors)
        if not author:
            continue
            
        if author.full_name and author.full_name != researcher.full_name:
            researcher.alternative_names.add(author.full_name)
        
        if paper.keywords:
            researcher.keywords.update(paper.keywords)
        
        if paper.subjects:
            researcher.subjects.update(paper.subjects)
        
        if paper.journal_name:
            researcher.journals.add(paper.journal_name)
        
        # Add external IDs
        if hasattr(author, 'identifiers') and author.identifiers:
            for id_type, id_value in author.identifiers.items():
                if id_type not in researcher.external_ids:
                    researcher.external_ids[id_type] = ExternalReference(
                        url=f"https://{id_type}.org/{id_value}",
                        name=id_type,
                        source="Publication Metadata"
                    )
        
        # Add grants from publication
        if paper.grants:
            for grant in paper.grants:
                # Only add if not already present (based on project number)
                if not any(g.id == grant.id for g in researcher.grants):
                    researcher.grants.append(grant) 