import json
from pathlib import Path
from typing import List, Dict
from orcid2taxid.core.models.schemas import AuthorMetadata, PaperMetadata

from orcid2taxid.data.clients.orcid_client import OrcidClient
from orcid2taxid.data.repositories.europe_pmc import EuropePMCRepository


def load_test_orcids(n: int = 5, keyword: str = None) -> List[str]:
    """
    Load the first n ORCIDs from the JSON file
    
    Args:
        n: Number of ORCIDs to load
        keyword: Optional keyword to specify which file to load from (e.g., 'jensen' loads from 'jensen_orcids.json')
    """
    filename = f"{keyword}_orcids.json" if keyword else "orcids.json"
    orcids_file = Path('tests/data') / filename
    
    if not orcids_file.exists():
        raise FileNotFoundError(f"ORCID list file not found at {orcids_file}")
        
    with open(orcids_file, 'r') as f:
        orcids = json.load(f)
    return orcids[:n]

def load_test_author_metadata(n: int = 5, force_refresh: bool = False, keyword: str = None) -> List[AuthorMetadata]:
    """
    Load test author metadata from a JSON file or regenerate it from ORCID API.
    
    Args:
        n: Number of author metadata records to load
        force_refresh: If True, regenerate the metadata by calling the ORCID API
        keyword: Optional keyword to specify which files to use (e.g., 'jensen' uses 'jensen_orcids.json' and saves to 'jensen_metadata.json')
        
    Returns:
        List of AuthorMetadata objects
    """
    filename = f"{keyword}_metadata.json" if keyword else "author_metadata.json"
    metadata_file = Path('tests/data') / filename
    
    if force_refresh or not metadata_file.exists():
        # Regenerate the metadata by calling the ORCID API
        orcids = load_test_orcids(n, keyword)
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
            json.dump([m.model_dump() for m in author_metadata_list], f, indent=2)
            
        return author_metadata_list
    
    # Load the metadata from the JSON file
    with open(metadata_file, 'r') as f:
        metadata_list = json.load(f)
    
    # If n is larger than available entries, regenerate additional entries
    if n > len(metadata_list):
        # Get additional ORCIDs beyond what we already have
        all_orcids = load_test_orcids(n, keyword)
        existing_orcids = [m.get('orcid') for m in metadata_list]
        new_orcids = [orcid for orcid in all_orcids if orcid not in existing_orcids]
        
        if new_orcids:
            client = OrcidClient()
            for orcid in new_orcids:
                try:
                    metadata = client.get_author_metadata(orcid)
                    metadata_list.append(metadata.model_dump())
                except Exception as e:
                    print(f"Error fetching metadata for ORCID {orcid}: {str(e)}")
            
            # Update the JSON file with the new entries
            with open(metadata_file, 'w') as f:
                json.dump(metadata_list, f, indent=2)
    
    # Convert the JSON data to AuthorMetadata objects (up to n entries)
    author_metadata_list = [AuthorMetadata(**m) for m in metadata_list[:n]]
    return author_metadata_list

def load_test_papers(n: int = 5, force_refresh: bool = False, keyword: str = None) -> List[PaperMetadata]:
    """
    Load test paper metadata from a JSON file or fetch them from Europe PMC API.
    
    Args:
        n: Number of ORCIDs to process
        force_refresh: If True, regenerate the papers by calling the Europe PMC API
        keyword: Optional keyword to specify which files to use (e.g., 'jensen' uses 'jensen_orcids.json' and saves to 'jensen_papers.json')
        
    Returns:
        List of PaperMetadata objects
    """
    filename = f"{keyword}_papers.json" if keyword else "papers.json"
    papers_file = Path('tests/data') / filename
    
    if force_refresh or not papers_file.exists():
        # Fetch papers by calling the Europe PMC API
        orcids = load_test_orcids(n, keyword)
        repository = EuropePMCRepository()
        papers_data = []
        
        for orcid in orcids:
            try:
                # Get publications for each ORCID
                publications = repository.get_publications_by_orcid(orcid, max_results=5)
                papers_data.extend([pub.model_dump() for pub in publications])
            except Exception as e:
                print(f"Error fetching papers for ORCID {orcid}: {str(e)}")
        
        # Save the fetched papers to the JSON file
        papers_file.parent.mkdir(parents=True, exist_ok=True)
        with open(papers_file, 'w') as f:
            json.dump(papers_data, f, indent=2)
            
        return [PaperMetadata(**p) for p in papers_data]
    
    # Load the papers from the JSON file
    with open(papers_file, 'r') as f:
        papers_data = json.load(f)
    
    # If n is larger than available entries, fetch additional entries
    if n * 5 > len(papers_data):  # Assuming ~5 papers per ORCID
        all_orcids = load_test_orcids(n, keyword)
        existing_papers = {p.get('doi') for p in papers_data if p.get('doi')}
        
        repository = EuropePMCRepository()
        for orcid in all_orcids:
            try:
                publications = repository.get_publications_by_orcid(orcid, max_results=5)
                for pub in publications:
                    if pub.doi and pub.doi not in existing_papers:
                        papers_data.append(pub.model_dump())
                        existing_papers.add(pub.doi)
            except Exception as e:
                print(f"Error fetching papers for ORCID {orcid}: {str(e)}")
        
        # Update the JSON file with new entries
        with open(papers_file, 'w') as f:
            json.dump(papers_data, f, indent=2)
    
    return [PaperMetadata(**p) for p in papers_data]

def load_test_abstracts(n: int = 5, force_refresh: bool = False, keyword: str = None) -> List[Dict[str, str]]:
    """
    Load test abstracts from a JSON file or fetch them from Europe PMC API.
    
    Args:
        n: Number of ORCIDs to process
        force_refresh: If True, regenerate the abstracts by calling the Europe PMC API
        keyword: Optional keyword to specify which files to use (e.g., 'jensen' uses 'jensen_orcids.json' and saves to 'jensen_abstracts.json')
        
    Returns:
        List of dictionaries containing ORCID and associated paper abstracts
    """
    filename = f"{keyword}_abstracts.json" if keyword else "abstracts.json"
    abstracts_file = Path('tests/data') / filename
    
    if force_refresh or not abstracts_file.exists():
        # Fetch abstracts by calling the Europe PMC API
        orcids = load_test_orcids(n, keyword)
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
        all_orcids = load_test_orcids(n, keyword)
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
    # Example usage with keyword
    abstracts = load_test_abstracts(n=10, force_refresh=True, keyword="jensen")
    # print(abstracts)