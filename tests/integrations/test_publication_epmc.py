import json
import pytest

from orcid2taxid.publication.integrations.epmc import (
    EpmcConfig,
    fetch_epmc_data,
    get_epmc_publications_by_orcid
)
from orcid2taxid.publication.schemas.base import PublicationRecord
from tests.api_test_cases import TEST_ORCID_ID
from tests.utils.utils import (
    get_responses_dir,
    save_response,
    load_response,
    compare_responses
)

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio

# Test data paths
EPMC_RESPONSES_DIR = get_responses_dir("publication_epmc")

# Timestamp fields to ignore in EPMC responses
EPMC_TIMESTAMP_FIELDS = ['lastModifiedDate', 'firstIndexDate', 'pubDate']

async def test_epmc_api_responses_consistency():
    """Test that EPMC API responses remain consistent with stored versions."""
    # Construct query parameters for ORCID search
    payload = {
        'query': f'AUTHORID:"{TEST_ORCID_ID}"',
        'resultType': 'core',
        'pageSize': 20,
        'format': 'json'
    }
    
    # Fetch current response
    current_response = await fetch_epmc_data(payload=payload)
    
    # Load stored response
    stored_response = load_response("publication_epmc", f"search_{TEST_ORCID_ID}.json")
    
    if stored_response is None:
        # First time running the test, save the response
        save_response("publication_epmc", f"search_{TEST_ORCID_ID}.json", current_response)
        pytest.skip("No stored response, saved current response")
        return
    
    # Compare responses
    assert compare_responses(stored_response, current_response, EPMC_TIMESTAMP_FIELDS), \
        "EPMC API response has changed from stored version"

async def test_epmc_publication_parsing():
    """Test that EPMC publication data can be parsed correctly."""
    config = EpmcConfig()
    
    # Fetch and parse publications
    publications = await get_epmc_publications_by_orcid(TEST_ORCID_ID, config=config)
    
    # Save parsed publications if they don't exist
    publications_path = EPMC_RESPONSES_DIR / f"parsed_publications_{TEST_ORCID_ID}.json"
    if not publications_path.exists():
        with open(publications_path, 'w', encoding='utf-8') as f:
            json.dump([pub.model_dump(mode='json') for pub in publications], f, indent=2)
        pytest.skip("No stored parsed publications, saved current publications")
    
    # Load stored publications
    with open(publications_path, 'r', encoding='utf-8') as f:
        stored_publications = [PublicationRecord.model_validate(pub) for pub in json.load(f)]
    
    # Compare publications
    assert [pub.model_dump(mode='json') for pub in publications] == \
           [pub.model_dump(mode='json') for pub in stored_publications], \
        "Parsed publications differ from stored version" 