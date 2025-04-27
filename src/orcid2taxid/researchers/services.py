from typing import List, Optional
from orcid2taxid.shared.schemas import (
    ResearcherProfile, Author,
    InstitutionalAffiliation, ExternalId
)
from orcid2taxid.publications.schemas import PublicationRecord
from orcid2taxid.researchers.integrations.orcid import OrcidClient
from orcid2taxid.publications.integrations.epmc import EuropePMCRepository

def get_researcher_by_orcid(orcid_id: str) -> ResearcherProfile:
    """Get researcher metadata from ORCID ID"""
    client = OrcidClient()
    metadata = client.get_author_metadata(orcid_id)
    return ResearcherProfile(**metadata.model_dump())

def find_publications(researcher: ResearcherProfile, max_results: Optional[int] = None) -> ResearcherProfile:
    """Fetch and add publications to researcher metadata"""
    epmc = EuropePMCRepository()
    client = OrcidClient()
    
    # Get publications from both sources
    epmc_papers = epmc.get_publications_by_orcid(researcher.orcid, max_results)
    orcid_papers = client.get_publications_by_orcid(researcher.orcid)
    
    # Deduplicate and update researcher
    unique_papers = _deduplicate_publications(epmc_papers + orcid_papers)
    researcher.publications = unique_papers[:max_results]
    
    # Enrich researcher metadata from publications
    _enrich_from_publications(researcher)
    return researcher

def _deduplicate_publications(publications: List[PublicationRecord]) -> List[PublicationRecord]:
    """Deduplicate publications based on DOI"""
    seen_dois = set()
    unique_pubs = []
    for paper in publications:
        if paper.doi and paper.doi in seen_dois:
            continue
        if paper.doi:
            seen_dois.add(paper.doi)
        unique_pubs.append(paper)
    return unique_pubs

def _find_matching_author(researcher: ResearcherProfile, authors: List[Author]) -> Optional[Author]:
    """Find the author entry that matches this researcher"""
    for author in authors:
        # Match by ORCID if available
        if author.orcid and author.orcid == researcher.orcid:
            return author
        
        # Match by email if available
        if (author.email and researcher.email and 
            author.email == researcher.email.address):
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
    """Enrich researcher metadata from publications"""
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
        if author.identifiers:
            for id_type, id_value in author.identifiers.items():
                if id_type not in researcher.external_ids:
                    researcher.external_ids[id_type] = ExternalId(value=id_value)
        
        # Add affiliations
        # for affiliation in author.affiliations:
        #     if affiliation:
        #         # Create AuthorAffiliation object
        #         aff = AuthorAffiliation(
        #             institution_name=affiliation,
        #             visibility='public'
        #         )
        #         # Only add if not already present
        #         if not any(a.institution_name == aff.institution_name for a in researcher.affiliations):
        #             researcher.affiliations.append(aff)

        # Add grants from publication
        for grant in paper.funding_info:
            # Only add if not already present (based on project number)
            if not any(g.project_num == grant.project_num for g in researcher.grants):
                researcher.grants.append(grant) 