import json
from pathlib import Path
from typing import List, Dict
from orcid2taxid.core.models.schemas import AuthorMetadata
from orcid2taxid.data.clients.orcid_client import OrcidClient
from orcid2taxid.data.repositories.europe_pmc import EuropePMCRepository


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

def load_test_abstracts(n: int = 5, force_refresh: bool = False) -> List[Dict[str, str]]:
    """
    Load test abstracts from a JSON file or fetch them from Europe PMC API.
    
    Args:
        n: Number of ORCIDs to process
        force_refresh: If True, regenerate the abstracts by calling the Europe PMC API
        
    Returns:
        List of dictionaries containing ORCID and associated paper abstracts
    """
    abstracts_file = Path('tests/data/abstracts.json')
    
    if force_refresh or not abstracts_file.exists():
        # Fetch abstracts by calling the Europe PMC API
        orcids = load_test_orcids(n)
        repository = EuropePMCRepository()
        abstracts_data = []
        
        for orcid in orcids:
            try:
                # Get publications for each ORCID
                publications = repository.get_publications_by_orcid(orcid, max_results=5)
                
                # Extract abstracts from publications
                orcid_abstracts = {
                    'orcid': orcid,
                    'abstracts': [
                        {
                            'title': pub.title,
                            'abstract': pub.abstract,
                            'doi': pub.doi,
                            'pmid': pub.pmid
                        }
                        for pub in publications
                        if pub.abstract  # Only include if abstract exists
                    ]
                }
                
                if orcid_abstracts['abstracts']:  # Only add if we found abstracts
                    abstracts_data.append(orcid_abstracts)
                    
            except Exception as e:
                print(f"Error fetching abstracts for ORCID {orcid}: {str(e)}")
        
        # Save the fetched abstracts to the JSON file
        abstracts_file.parent.mkdir(parents=True, exist_ok=True)
        with open(abstracts_file, 'w') as f:
            json.dump(abstracts_data, f, indent=2)
            
        return abstracts_data[:n]
    
    # Load the abstracts from the JSON file
    with open(abstracts_file, 'r') as f:
        abstracts_data = json.load(f)
    
    # If n is larger than available entries, fetch additional entries
    if n > len(abstracts_data):
        all_orcids = load_test_orcids(n)
        existing_orcids = [a['orcid'] for a in abstracts_data]
        new_orcids = [orcid for orcid in all_orcids if orcid not in existing_orcids]
        
        if new_orcids:
            repository = EuropePMCRepository()
            for orcid in new_orcids:
                try:
                    publications = repository.get_publications_by_orcid(orcid, max_results=5)
                    orcid_abstracts = {
                        'orcid': orcid,
                        'abstracts': [
                            {
                                'title': pub.title,
                                'abstract': pub.abstract,
                                'doi': pub.doi,
                                'pmid': pub.pmid
                            }
                            for pub in publications
                            if pub.abstract
                        ]
                    }
                    
                    if orcid_abstracts['abstracts']:
                        abstracts_data.append(orcid_abstracts)
                        
                except Exception as e:
                    print(f"Error fetching abstracts for ORCID {orcid}: {str(e)}")
            
            # Update the JSON file with new entries
            with open(abstracts_file, 'w') as f:
                json.dump(abstracts_data, f, indent=2)
    
    return abstracts_data[:n]

if __name__ == "__main__":
    abstracts = load_test_abstracts(n=10, force_refresh=True)
    # print(abstracts)