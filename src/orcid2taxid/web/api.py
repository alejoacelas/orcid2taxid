from fastapi import FastAPI
from typing import List
from orcid2taxid.core.models.schemas import PaperMetadata
from orcid2taxid.integrations.europe_pmc import EuropePMCRepository
from orcid2taxid.core.operations.paper import get_taxonomy_info

app = FastAPI()

@app.get("/orcid2taxid/{orcid_id}", response_model=List[PaperMetadata])
async def get_papers_with_taxids(orcid_id: str, max_results: int = 20):
    # Initialize repositories
    europe_pmc = EuropePMCRepository()
    
    # Get publications
    papers = europe_pmc.get_publications_by_orcid(orcid_id, max_results=max_results)
    
    # Process each paper to get taxonomy info
    papers_with_taxids = []
    for paper in papers:
        paper_with_tax = get_taxonomy_info(paper)
        if paper_with_tax.taxids:  # Only include papers that have taxids
            papers_with_taxids.append(paper_with_tax)
            
    return papers_with_taxids
