# %%
from src.publications.repositories.europe_pmc import EuropePMCFetcher
from src.publications.repositories.biorxiv import BiorxivFetcher
from src.orcid.orcid import OrcidClient
from src.schemas.schemas import AuthorMetadata, AuthorAffiliation
from datetime import date
import json
from tests.utils.utils import load_test_orcids

# %%
# def print_comparison(title: str, formatted_data, raw_data):
#     """Helper function to print formatted and raw data side by side"""
#     print(f"\n{'='*40} {title} {'='*40}")
#     print("\nFormatted Response:")
#     if isinstance(formatted_data, list):
#         for i, item in enumerate(formatted_data[:3], 1):  # Show first 3 items
#             print(f"\nItem {i}:")
#             print(json.dumps(item.model_dump(), indent=2, default=lambda o: o.isoformat() if isinstance(o, date) else str(o)))
#         if len(formatted_data) > 3:
#             print(f"\n... and {len(formatted_data) - 3} more items")
#     else:
#         print(json.dumps(formatted_data.model_dump(), indent=2, default=lambda o: o.isoformat() if isinstance(o, date) else str(o)))
    
#     print("\nRaw Response:")
#     print(json.dumps(raw_data, indent=2))
#     print(f"\n{'='*90}\n")

def test_orcid_fetcher():
    # Initialize the fetcher
    fetcher = OrcidClient()  # No API key needed for public endpoints
    
    # Load test ORCIDs
    test_orcids = load_test_orcids()
    
    for test_orcid in test_orcids:
        print(f"\nTesting ORCID fetcher for {test_orcid}...")
        
        # Test researcher info fetching
        print("\nTesting researcher info fetching...")
        researcher_info = fetcher.fetch_researcher_info(test_orcid)
        
        print("Researcher Info:")
        print(researcher_info.model_dump_json(indent=2))
        
        # Test publications fetching
        print("\nTesting publications fetching...")
        publications = fetcher.fetch_publications(test_orcid)
        
        print(f"\nFound {len(publications)} publications")
        for i, pub in enumerate(publications[:5], 1):  # Show first 5 publications
            print(f"\nPublication {i}:")
            print(f"Title: {pub.title}")
            print(f"Type: {pub.type or 'N/A'}")
            print(f"Date: {pub.publication_date or 'N/A'}")
            print(f"Journal: {pub.journal or 'N/A'}")
            print(f"DOI: {pub.doi or 'N/A'}")
            print(f"Source: {pub.repository_source}")
            if pub.external_ids:
                print("External IDs:", json.dumps({k: v.dict() for k, v in pub.external_ids.items()}, indent=2))
        
        print("\n" + "="*80)

def test_europepmc_fetcher():
    """Test Europe PMC fetcher with both formatted and raw responses"""
    fetcher = EuropePMCFetcher()
    test_orcids = load_test_orcids(2)  # Test with 2 ORCIDs
    
    # Test ORCID search
    for test_orcid in test_orcids:
        print(f"\nTesting Europe PMC ORCID search for {test_orcid}...")
        formatted_papers = fetcher.search_by_orcid(test_orcid, max_results=5)
        raw_response = fetcher.get_raw_orcid_results(test_orcid, max_results=5)
        
# %%
