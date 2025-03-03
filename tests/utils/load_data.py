import json
from pathlib import Path
from typing import List
from orcid2taxid.core.models.schemas import AuthorMetadata
from orcid2taxid.data.clients.orcid_client import OrcidClient


def load_test_orcids(n: int = 5) -> List[str]:
    """Load the first n ORCIDs from the JSON file"""
    orcids_file = Path('tests/data/orcids.json')
    if not orcids_file.exists():
        raise FileNotFoundError("ORCID list file not found at tests/data/orcids.json")
        
    with open(orcids_file, 'r') as f:
        orcids = json.load(f)
    return orcids[:n]

def load_test_author_metadata(n: int = 5, force_refresh: bool = False) -> List[AuthorMetadata]:
    """
    Load test author metadata from a JSON file or regenerate it from ORCID API.
    
    Args:
        n: Number of author metadata records to load
        regenerate: If True, regenerate the metadata by calling the ORCID API
        
    Returns:
        List of AuthorMetadata objects
    """
    metadata_file = Path('tests/data/author_metadata.json')
    
    if force_refresh or not metadata_file.exists():
        # Regenerate the metadata by calling the ORCID API
        
        orcids = load_test_orcids(n)
        client = OrcidClient()
        author_metadata_list = []
        
        for orcid in orcids:
            try:
                metadata = client.get_author_metadata(orcid)
                author_metadata_list.append(metadata)
            except Exception as e:
                print(f"Error fetching metadata for ORCID {orcid}: {str(e)}")
        
        # Save the regenerated metadata to the JSON file
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'w') as f:
            json.dump([m.dict() for m in author_metadata_list], f, indent=2)
            
        return author_metadata_list
    
    # Load the metadata from the JSON file
    with open(metadata_file, 'r') as f:
        metadata_list = json.load(f)
    
    # If n is larger than available entries, regenerate additional entries
    if n > len(metadata_list):
        
        # Get additional ORCIDs beyond what we already have
        all_orcids = load_test_orcids(n)
        existing_orcids = [m.get('orcid') for m in metadata_list]
        new_orcids = [orcid for orcid in all_orcids if orcid not in existing_orcids]
        
        if new_orcids:
            client = OrcidClient()
            for orcid in new_orcids:
                try:
                    metadata = client.get_author_metadata(orcid)
                    metadata_list.append(metadata.dict())
                except Exception as e:
                    print(f"Error fetching metadata for ORCID {orcid}: {str(e)}")
            
            # Update the JSON file with the new entries
            with open(metadata_file, 'w') as f:
                json.dump(metadata_list, f, indent=2)
    
    # Convert the JSON data to AuthorMetadata objects (up to n entries)
    author_metadata_list = [AuthorMetadata(**m) for m in metadata_list[:n]]
    return author_metadata_list