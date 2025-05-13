import asyncio
from typing import List
from fastapi import FastAPI, HTTPException

from orcid2taxid.researcher.schemas.base import CustomerProfile, OrganismAggregation
from orcid2taxid.researcher.services import get_customer_profile, collect_customer_publications
from orcid2taxid.publication.services import collect_publication_organisms
from orcid2taxid.grant.services import find_grants
from orcid2taxid.shared.schemas import ResearcherID

app = FastAPI(
    title="ROSE Scout API",
    description="API for retrieving researcher information including publications, grants, and organism data",
    version="0.1.0"
)

@app.get("/researcher/{orcid}", response_model=CustomerProfile)
async def get_researcher_info(orcid: str):
    """
    Get comprehensive researcher information including:
    - Basic profile information
    - Publications with organism data
    - Research grants
    - Education and employment history
    
    Args:
        orcid: The researcher's ORCID ID
        
    Returns:
        CustomerProfile: Complete researcher profile with all available information
    """
    try:
        # Get basic researcher profile
        customer_id = ResearcherID(orcid=orcid)
        researcher = await get_customer_profile(customer_id)
        
        # Get publications
        researcher = await collect_customer_publications(researcher, max_results=50)
        
        # Process publications to extract organisms
        if researcher.publications:
            tasks = [collect_publication_organisms(paper) for paper in researcher.publications]
            processed_papers = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update papers in researcher object
            for i, processed_paper in enumerate(processed_papers):
                if not isinstance(processed_paper, Exception):
                    researcher.publications[i] = processed_paper
        
        # Get grants
        researcher = await find_grants(researcher, max_results=50)
        
        return researcher
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/researcher/{orcid}/organisms", response_model=List[OrganismAggregation])
async def get_researcher_organisms(orcid: str):
    """
    Get aggregated information about organisms that a researcher has worked with.
    
    Args:
        orcid: The researcher's ORCID ID
        
    Returns:
        List[OrganismAggregation]: List of organisms with aggregated information including:
        - Scientific name and taxonomy ID
        - Whether it's a controlled agent
        - List of publications mentioning the organism
        - Total number of mentions across publications
        - Date range of mentions (first to last)
    """
    try:
        # Get basic researcher profile
        customer_id = ResearcherID(orcid=orcid)
        researcher = await get_customer_profile(customer_id)
        
        # Get publications
        researcher = await collect_customer_publications(researcher, max_results=50)
        
        # Process publications to extract organisms
        if not researcher.publications:
            return []
            
        tasks = [collect_publication_organisms(paper) for paper in researcher.publications]
        processed_papers = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update papers in researcher object
        for i, processed_paper in enumerate(processed_papers):
            if not isinstance(processed_paper, Exception):
                researcher.publications[i] = processed_paper
        
        # Get organism aggregations
        return researcher.get_organism_aggregations()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

