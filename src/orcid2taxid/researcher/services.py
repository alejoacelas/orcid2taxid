from typing import List, Optional
from orcid2taxid.researcher.schemas import CustomerProfile
from orcid2taxid.publication.schemas import PublicationRecord
from orcid2taxid.shared.schemas import ResearcherID
from orcid2taxid.publication.integrations.epmc import get_epmc_publications_by_orcid
from orcid2taxid.researcher.integrations.orcid import get_orcid_profile
from orcid2taxid.core.logging import log_event, get_logger

logger = get_logger(__name__)

@log_event(__name__)
async def get_customer_profile(customer_id: ResearcherID) -> CustomerProfile:
    """
    Get researcher metadata from ORCID ID
    
    Args:
        orcid_id: The ORCID identifier for the researcher
        
    Returns:
        ResearcherProfile: Complete researcher profile with metadata
    """
    if customer_id.orcid:
        profile = await get_orcid_profile(customer_id.orcid)
    # if customer_id.email:
    #     # TODO: Implement email lookup with o3
    #     pass
    # # TODO: Implement profile merging
    else:
        raise ValueError("ORCID ID is required. Customer profile by email not yet implemented.")
    
    return profile

@log_event(__name__)
async def collect_customer_publications(
    customer: CustomerProfile, 
    max_results: Optional[int] = None
) -> CustomerProfile:
    """
    Fetch and add publications to customer metadata
    
    Args:
        researcher: The researcher profile to enrich
        max_results: Maximum number of publications to fetch
        
    Returns:
        CustomerProfile: The enriched customer profile
    """
    # Get publications from Europe PMC source
    epmc_papers = await get_epmc_publications_by_orcid(customer.researcher_id.orcid, max_results)
    
    # Get publications from ORCID (already in the profile)
    orcid_papers = customer.publications if hasattr(customer, 'publications') else []
    
    # Deduplicate and update researcher
    unique_papers = _deduplicate_publications(epmc_papers + orcid_papers)
    if max_results is not None:
        unique_papers = unique_papers[:max_results]
    
    customer.publications = unique_papers
    
    # Enrich customer metadata from publications
    _enrich_profile_from_publications(customer)
    return customer

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

def _enrich_profile_from_publications(customer: CustomerProfile) -> None:
    """
    Enrich customer metadata from publications
    
    Args:
        researcher: The researcher profile to enrich
    """
    for paper in customer.publications:
        # Find matching author using next() with a generator expression
        author = next(
            (author for author in paper.authors 
             if customer.researcher_id.is_same_person(author.researcher_id)),
            None
        )
        if not author:
            continue
            
        if paper.keywords:
            customer.description.extend("Keywords", ', '.join(paper.keywords))
        
        if paper.subjects:
            customer.description.extend("Subjects", ', '.join(paper.subjects))
        
        if paper.journal_name:
            customer.description.extend("Journal", paper.journal_name)
        
        # Add external IDs
        if author.external_references:
            for ref in author.external_references:
                # Check if this external ID already exists
                if not any(existing_ref.name == ref.name for existing_ref in customer.external_references):
                    customer.external_references.append(ref)
        
        # Add grants from publication
        if paper.grants:
            for grant in paper.grants:
                # Only add if not already present (based on project number)
                if not any(g.id == grant.id for g in customer.grants):
                    customer.grants.append(grant) 