from orcid2taxid.core.models.schemas import GrantMetadata, ResearcherMetadata
from orcid2taxid.analysis.extraction.grant import GrantExtractor
from orcid2taxid.integrations.nih_reporter import NIHReporterRepository
from orcid2taxid.integrations.nsf_grants import NSFRepository
from orcid2taxid.integrations.europe_pmc import EuropePMCRepository
from typing import List, Set

def get_grant_metadata(grant: GrantMetadata) -> GrantMetadata:
    """Extract metadata from grant title and abstract"""
    if not grant.project_terms:
        extractor = GrantExtractor()
        grant.project_terms = extractor.extract_terms_from_abstract(grant)
    return grant

def _is_nih_grant(funder: str) -> bool:
    """Check if a grant is from NIH"""
    nih_keywords = {'nih', 'national institutes of health', 'national institute of health'}
    return any(keyword in funder.lower() for keyword in nih_keywords)

def _is_nsf_grant(funder: str) -> bool:
    """Check if a grant is from NSF"""
    nsf_keywords = {'nsf', 'national science foundation'}
    return any(keyword in funder.lower() for keyword in nsf_keywords)

def _enhance_grant_metadata(grant: GrantMetadata) -> GrantMetadata:
    """Enhance grant metadata using NIH/NSF APIs if applicable"""
    if not grant.project_num:
        return grant
        
    nih = NIHReporterRepository()
    nsf = NSFRepository()
    
    # Try to enhance with NIH data if it's an NIH grant
    if _is_nih_grant(grant.funder or ''):
        nih_grant = nih.get_grant_by_number(grant.project_num)
        if nih_grant:
            return nih_grant
            
    # Try to enhance with NSF data if it's an NSF grant
    if _is_nsf_grant(grant.funder or ''):
        nsf_grant = nsf.get_grant_by_number(grant.project_num)
        if nsf_grant:
            return nsf_grant
            
    return grant

def find_grants(researcher: ResearcherMetadata, max_results: int = 20) -> ResearcherMetadata:
    """Fetch and add grants to researcher metadata"""
    nih = NIHReporterRepository()
    nsf = NSFRepository()
    epmc = EuropePMCRepository()
    
    # Get grants from publications - using a list instead of a set to avoid hash errors
    publication_grants: List[GrantMetadata] = []
    for publication in researcher.publications:
        for grant in publication.funding_info:
            # Enhance grant metadata if it's from NIH/NSF
            enhanced_grant = _enhance_grant_metadata(grant)
            if enhanced_grant not in publication_grants:
                publication_grants.append(enhanced_grant)
    
    # Get grants from NIH Reporter by PI name
    researcher_name = f"{researcher.given_name} {researcher.family_name}"
    nih_grants = nih.get_funding_by_pi_name(researcher_name, max_results)
    
    # Get grants from NSF by PI name
    nsf_grants = nsf.get_funding_by_pi_name(researcher_name, max_results)
    
    # Combine all grants
    all_grants = publication_grants + nih_grants + nsf_grants
    
    # Remove duplicates based on project number
    unique_grants = {}
    for grant in all_grants:
        if grant.project_num:
            unique_grants[grant.project_num] = grant
        else:
            # For grants without project numbers, use title as key
            unique_grants[grant.project_title] = grant
    
    # Update researcher with unique grants
    researcher.grants = list(unique_grants.values())
    
    return researcher 