import json
from pathlib import Path
from typing import List
from orcid2taxid.core.models.schemas import (
    ResearcherMetadata, 
    PaperMetadata,
    CustomBaseModel
)
from orcid2taxid.integrations.orcid import OrcidClient
from orcid2taxid.integrations.epmc_publications import EuropePMCRepository

# Specific container models for each type
class ResearcherList(CustomBaseModel):
    items: List[ResearcherMetadata]

class PaperList(CustomBaseModel):
    items: List[PaperMetadata]

# Path constants
TEST_DATA_DIR = Path('tests/data')

def load_test_orcids(n: int = 5, keyword: str = 'virology') -> List[str]:
    """Load the first n ORCIDs from the JSON file"""
    filename = f"{keyword}_orcids.json"
    orcids_file = TEST_DATA_DIR / filename
    
    if not orcids_file.exists():
        raise FileNotFoundError(f"ORCID list file not found at {orcids_file}")
        
    with open(orcids_file, 'r') as f:
        orcids = json.load(f)
    return orcids[:n]

def load_test_researchers(n: int = 5, force_refresh: bool = False, keyword: str = 'virology') -> List[ResearcherMetadata]:
    """Load test author metadata from a JSON file or regenerate it from ORCID API."""
    filename = f"{keyword}_author_metadata.json"
    metadata_file = TEST_DATA_DIR / filename
    
    if force_refresh or not metadata_file.exists():
        # Fetch new metadata
        orcids = load_test_orcids(n, keyword)
        client = OrcidClient()
        metadata_list = []
        
        for orcid in orcids:
            try:
                metadata = client.get_author_metadata(orcid)
                metadata_list.append(metadata)
            except Exception as e:
                print(f"Error fetching metadata for ORCID {orcid}: {str(e)}")
        
        # Save the metadata with proper JSON formatting
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'w') as f:
            container = ResearcherList(items=metadata_list)
            f.write(container.model_dump_json(indent=2))
            
        return metadata_list
    
    # Load from file
    with open(metadata_file, 'r') as f:
        json_data = f.read()
        container = ResearcherList.model_validate_json(json_data)
        return container.items[:n]

def load_test_papers(n: int = 5, force_refresh: bool = False, keyword: str = 'virology') -> List[PaperMetadata]:
    """Load test paper metadata from a JSON file or fetch them from Europe PMC API."""
    filename = f"{keyword}_papers.json"
    papers_file = TEST_DATA_DIR / filename
    
    if force_refresh or not papers_file.exists():
        # Fetch new papers
        orcids = load_test_orcids(n, keyword)
        repository = EuropePMCRepository()
        papers_list = []
        
        for orcid in orcids:
            try:
                publications = repository.get_publications_by_orcid(orcid, max_results=5)
                papers_list.extend(publications)
            except Exception as e:
                print(f"Error fetching papers for ORCID {orcid}: {str(e)}")
        
        # Save the papers with proper JSON formatting
        papers_file.parent.mkdir(parents=True, exist_ok=True)
        with open(papers_file, 'w') as f:
            container = PaperList(items=papers_list)
            f.write(container.model_dump_json(indent=2))
            
        return papers_list[:n]
    
    # Load from file
    try:
        with open(papers_file, 'r') as f:
            json_data = f.read()
            container = PaperList.model_validate_json(json_data)
            return container.items[:n]
    except json.JSONDecodeError:
        print(f"Error reading papers file {papers_file}. Forcing refresh...")
        return load_test_papers(n=n, force_refresh=True, keyword=keyword)
    except Exception as e:
        print(f"Unexpected error reading papers file: {str(e)}. Forcing refresh...")
        return load_test_papers(n=n, force_refresh=True, keyword=keyword)

if __name__ == "__main__":
    # Refresh metadata for up to 50 ORCIDs
    for kw in ['virology', 'jensen']:
        print(f"Refreshing researcher and paper metadata for {kw}...")
        
        # First refresh researcher metadata
        print("\nFetching researcher metadata...")
        researchers = load_test_researchers(n=50, force_refresh=True, keyword=kw)
        print(f"Successfully fetched metadata for {len(researchers)} researchers")
        
        # Then refresh paper metadata
        print("\nFetching paper metadata...")
        papers = load_test_papers(n=50, force_refresh=True, keyword=kw)
        print(f"Successfully fetched metadata for {len(papers)} papers")
        
    print("\nMetadata refresh complete!")
