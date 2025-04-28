import json
import pytest

from orcid2taxid.grant.integrations.nih import (
    NIHConfig,
    fetch_nih_data,
    get_nih_grant_by_number,
    get_nih_grants_by_pi_name,
    get_nih_grants_by_organization
)
from orcid2taxid.grant.schemas.base import GrantRecord
from tests.api_test_cases import (
    TEST_NIH_GRANT_ID,
    TEST_NIH_RECIPIENT_ORGANIZATION,
    TEST_RESEARCHER_NAME
)
from tests.utils.utils import (
    get_responses_dir,
    save_response,
    load_response,
    compare_responses
)

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio

# Test data paths
NIH_RESPONSES_DIR = get_responses_dir("grant_nih")

# Timestamp fields to ignore in NIH responses
NIH_TIMESTAMP_FIELDS = ['award_notice_date', 'project_start_date', 'project_end_date', 'budget_start', 'budget_end']

async def test_nih_api_responses_consistency():
    """Test that NIH Reporter API responses remain consistent with stored versions."""
    # Construct query parameters for grant search
    payload = {
        "criteria": {
            "project_nums": [TEST_NIH_GRANT_ID]
        },
        "limit": 1,
        "offset": 0
    }
    
    # Fetch current response
    current_response = await fetch_nih_data(payload=payload)
    
    # Load stored response
    stored_response = load_response("grant_nih", f"grant_{TEST_NIH_GRANT_ID}.json")
    
    if stored_response is None:
        # First time running the test, save the response
        save_response("grant_nih", f"grant_{TEST_NIH_GRANT_ID}.json", current_response)
        pytest.skip("No stored response, saved current response")
        return
    
    # Compare responses
    assert compare_responses(stored_response, current_response, NIH_TIMESTAMP_FIELDS), \
        "NIH Reporter API response has changed from stored version"

async def test_nih_grant_parsing():
    """Test that NIH grant data can be parsed correctly."""
    config = NIHConfig()
    
    # Fetch and parse grant
    grant = await get_nih_grant_by_number(TEST_NIH_GRANT_ID, config=config)
    
    # Save parsed grant if it doesn't exist
    grant_path = NIH_RESPONSES_DIR / f"parsed_grant_{TEST_NIH_GRANT_ID}.json"
    if not grant_path.exists():
        with open(grant_path, 'w', encoding='utf-8') as f:
            json.dump(grant.model_dump(mode='json'), f, indent=2)
        pytest.skip("No stored parsed grant, saved current grant")
        return
    
    # Load stored grant
    with open(grant_path, 'r', encoding='utf-8') as f:
        stored_grant = GrantRecord.model_validate(json.load(f))
    
    # Compare grants
    assert grant.model_dump(mode='json') == stored_grant.model_dump(mode='json'), \
        "Parsed grant differs from stored version"

async def test_nih_search_by_organization():
    """Test searching NIH grants by organization."""
    config = NIHConfig()
    
    # Get grants by organization
    grants = await get_nih_grants_by_organization(TEST_NIH_RECIPIENT_ORGANIZATION, max_results=5, config=config)
    
    # Make sure we got results
    assert len(grants) > 0, f"No grants found for organization: {TEST_NIH_RECIPIENT_ORGANIZATION}"
    
    # Verify each grant has key fields
    for grant in grants:
        assert grant.id, "Grant missing ID"
        assert grant.recipient, "Grant missing recipient organization"

async def test_nih_search_by_pi_name():
    """Test searching NIH grants by PI name."""
    config = NIHConfig()
    
    # Get grants by PI name
    grants = await get_nih_grants_by_pi_name(TEST_RESEARCHER_NAME, max_results=5, config=config)
    
    # Make sure we got results
    assert len(grants) > 0, f"No grants found for PI name: {TEST_RESEARCHER_NAME}"
    
    # Verify each grant has key fields
    for grant in grants:
        assert grant.id, "Grant missing ID"
        assert grant.principal_investigators, "Grant missing principal investigators" 