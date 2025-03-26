from orcid2taxid.core.models.schemas import PaperMetadata
from orcid2taxid.analysis.extraction.paper import PaperExtractor
from orcid2taxid.integrations.ncbi import TaxIDLookup

def get_organisms(paper: PaperMetadata) -> PaperMetadata:
    """Extract organisms from paper title and abstract"""
    if not paper.organisms:
        extractor = PaperExtractor()
        paper.organisms = extractor.extract_organisms_from_abstract(paper)
    return paper

def get_classification(paper: PaperMetadata) -> PaperMetadata:
    """Extract classification from paper title and abstract"""
    if not paper.classification:
        extractor = PaperExtractor()
        paper.classification = extractor.extract_classification_from_abstract(paper)
    return paper

def get_taxonomy_info(paper: PaperMetadata) -> PaperMetadata:
    """Get taxonomy information for organisms in the paper"""
    paper = get_organisms(paper)
    lookup = TaxIDLookup()
    
    # Update each organism mention with its taxonomy info
    for organism in paper.organisms:
        if not organism.taxonomy_info:
            organism.taxonomy_info = lookup.get_taxid(organism.searchable_name)
    
    return paper

def find_full_text_url(paper: PaperMetadata) -> PaperMetadata:
    """Find the full text URL for the paper using Unpaywall"""
    # TODO: Implement Unpaywall integration
    return paper 