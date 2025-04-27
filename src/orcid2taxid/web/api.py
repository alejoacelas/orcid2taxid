from fastapi import FastAPI
from typing import List
from orcid2taxid.core.models.customer import PublicationRecord
from orcid2taxid.publications.integrations.epmc import EuropePMCRepository
from orcid2taxid.publications.services import get_taxonomy_info

app = FastAPI()

@app.get("/orcid2taxid/{orcid_id}", response_model=List[PublicationRecord])
async def get_papers_with_taxids(orcid_id: str, max_results: int = 20):
    """Get papers with taxonomy information for a given ORCID ID."""
    repository = EuropePMCRepository()
    papers = await repository.get_publications_by_orcid(orcid_id, max_results=max_results)
    
    # Get papers that have organisms with taxonomy info
    papers_with_taxids = []
    for paper in papers:
        if any(org.taxonomy_info for org in paper.organisms):  # Only include papers that have organisms with taxonomy info
            papers_with_taxids.append(paper)
    
    return papers_with_taxids
