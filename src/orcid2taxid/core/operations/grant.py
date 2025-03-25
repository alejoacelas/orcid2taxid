from orcid2taxid.core.models.schemas import GrantMetadata, ResearcherMetadata
from orcid2taxid.analysis.extraction.grant import GrantExtractor
from orcid2taxid.integrations.nih_reporter import NIHReporterRepository

def get_grant_metadata(grant: GrantMetadata) -> GrantMetadata:
    """Extract metadata from grant title and abstract"""
    if not grant.project_terms:
        extractor = GrantExtractor()
        grant.project_terms = extractor.extract_terms_from_abstract(grant)
    return grant

def find_grants(researcher: ResearcherMetadata, max_results: int = 20) -> ResearcherMetadata:
    """Fetch and add grants to researcher metadata"""
    nih = NIHReporterRepository()
    
    # Get grants from NIH Reporter
    researcher_name = f"{researcher.given_name} {researcher.family_name}"
    nih_grants = nih.get_funding_by_pi_name(researcher_name, max_results)
    
    # Update researcher with grants
    researcher.grants = nih_grants
    
    # Enrich grant metadata
    # for grant in researcher.grants:
    #     grant = get_grant_metadata(grant)
    
    return researcher 