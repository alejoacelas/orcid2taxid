import json
import pytest

from orcid2taxid.researcher.integrations.orcid import (
    OrcidConfig,
    fetch_orcid_data,
    get_profile,
    parse_affiliations
)
from orcid2taxid.researcher.schemas.base import CustomerProfile
from tests.integrations.api_test_cases import TEST_ORCID_ID
from tests.utils.utils import (
    get_responses_dir,
    save_response,
    load_response,
    compare_responses
)

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio

# Test data paths
ORCID_RESPONSES_DIR = get_responses_dir("researcher_orcid")

# Timestamp fields to ignore in ORCID responses
ORCID_TIMESTAMP_FIELDS = ['last-modified-date', 'created-date', 'updated-date']

async def test_orcid_api_responses_consistency():
    """Test that ORCID API responses remain consistent with stored versions."""
    config = OrcidConfig()
    endpoints = ["person", "works", "educations", "employments"]
    
    for endpoint in endpoints:
        # Fetch current response
        current_response = await fetch_orcid_data(TEST_ORCID_ID, endpoint, config)
        
        # Load stored response
        stored_response = load_response("researcher_orcid", f"{endpoint}_{TEST_ORCID_ID}.json")
        
        if stored_response is None:
            # First time running the test, save the response
            save_response("researcher_orcid", f"{endpoint}_{TEST_ORCID_ID}.json", current_response)
            pytest.skip(f"No stored response for {endpoint}, saved current response")
            continue
        
        # Compare responses
        assert compare_responses(stored_response, current_response, ORCID_TIMESTAMP_FIELDS), \
            f"ORCID API response for {endpoint} has changed from stored version"

async def test_orcid_profile_parsing():
    """Test that ORCID profile data can be parsed correctly."""
    config = OrcidConfig()
    
    # Fetch and parse profile
    profile = await get_profile(TEST_ORCID_ID, config)
    
    # Save parsed profile if it doesn't exist
    profile_path = ORCID_RESPONSES_DIR / f"parsed_profile_{TEST_ORCID_ID}.json"
    if not profile_path.exists():
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(mode='json'), f, indent=2)
        pytest.skip("No stored parsed profile, saved current profile")
    
    # Load stored profile
    with open(profile_path, 'r', encoding='utf-8') as f:
        stored_profile = CustomerProfile.model_validate(json.load(f))
    
    # Compare profiles
    assert profile.model_dump(mode='json') == stored_profile.model_dump(mode='json'), \
        "Parsed profile differs from stored version"

async def test_affiliation_parsing():
    """Test that ORCID affiliations can be parsed correctly."""
    config = OrcidConfig()
    
    # Fetch education and employment data
    education_data = await fetch_orcid_data(TEST_ORCID_ID, "educations", config)
    employment_data = await fetch_orcid_data(TEST_ORCID_ID, "employments", config)
    
    # Parse affiliations
    educations = parse_affiliations(education_data)
    employments = parse_affiliations(employment_data)
    
    # Save parsed affiliations if they don't exist
    affiliations_path = ORCID_RESPONSES_DIR / f"parsed_affiliations_{TEST_ORCID_ID}.json"
    if not affiliations_path.exists():
        with open(affiliations_path, 'w', encoding='utf-8') as f:
            json.dump({
                'educations': [edu.model_dump(mode='json') for edu in educations],
                'employments': [emp.model_dump(mode='json') for emp in employments]
            }, f, indent=2)
        pytest.skip("No stored parsed affiliations, saved current affiliations")
    
    # Load stored affiliations
    with open(affiliations_path, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)
        stored_educations = [parse_affiliations({'affiliation-group': [{'summaries': [{'education-summary': edu}]}]})[0] 
                           for edu in stored_data['educations']]
        stored_employments = [parse_affiliations({'affiliation-group': [{'summaries': [{'employment-summary': emp}]}]})[0] 
                            for emp in stored_data['employments']]
    
    # Compare affiliations
    assert [edu.model_dump(mode='json') for edu in educations] == [edu.model_dump(mode='json') for edu in stored_educations], \
        "Parsed educations differ from stored version"
    assert [emp.model_dump(mode='json') for emp in employments] == [emp.model_dump(mode='json') for emp in stored_employments], \
        "Parsed employments differ from stored version" 