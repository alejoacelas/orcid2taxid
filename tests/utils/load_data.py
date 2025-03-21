import json
from pathlib import Path
from typing import List, Dict
from orcid2taxid.core.models.schemas import ResearcherMetadata, PaperMetadata
from orcid2taxid.integrations.orcid import OrcidClient
from orcid2taxid.integrations.europe_pmc import EuropePMCRepository

# Path constants
TEST_DATA_DIR = Path('tests/data')

def load_test_orcids(n: int = 5, keyword: str = 'virology') -> List[str]:
    """Load the first n ORCIDs from the JSON file"""
    filename = f"{keyword}_orcids.json" if keyword else "orcids.json"
    orcids_file = TEST_DATA_DIR / filename
    
    if not orcids_file.exists():
        raise FileNotFoundError(f"ORCID list file not found at {orcids_file}")
        
    with open(orcids_file, 'r') as f:
        orcids = json.load(f)
    return orcids[:n]

def load_test_researchers(n: int = 5, force_refresh: bool = False, keyword: str = 'virology') -> List[ResearcherMetadata]:
    """Load test author metadata from a JSON file or regenerate it from ORCID API."""
    filename = f"{keyword}_author_metadata.json" if keyword else "author_metadata.json"
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
        
        # Save the metadata using model_dump_json()
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'w') as f:
            json_data = [m.model_dump_json() for m in metadata_list]
            f.write(f"[{','.join(json_data)}]")
            
        return metadata_list
    
    # Load from file
    with open(metadata_file, 'r') as f:
        metadata_list = json.load(f)
    return [ResearcherMetadata(**m) for m in metadata_list[:n]]

def load_test_papers(n: int = 5, force_refresh: bool = False, keyword: str = 'virology') -> List[PaperMetadata]:
    """Load test paper metadata from a JSON file or fetch them from Europe PMC API."""
    filename = f"{keyword}_papers.json" if keyword else "papers.json"
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
        
        # Save the papers using model_dump_json()
        papers_file.parent.mkdir(parents=True, exist_ok=True)
        with open(papers_file, 'w') as f:
            json_data = [p.model_dump_json() for p in papers_list]
            f.write(f"[{','.join(json_data)}]")
            
        return papers_list[:n]
    
    # Load from file
    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
        return [PaperMetadata(**p) for p in papers_data[:n]]
    except json.JSONDecodeError:
        print(f"Error reading papers file {papers_file}. Forcing refresh...")
        return load_test_papers(n=n, force_refresh=True, keyword=keyword)
    except Exception as e:
        print(f"Unexpected error reading papers file: {str(e)}. Forcing refresh...")
        return load_test_papers(n=n, force_refresh=True, keyword=keyword)
