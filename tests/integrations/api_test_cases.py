"""Test identifiers and queries used across test suite."""

# Single identifiers for direct test cases
TEST_ORCID_ID = "0000-0002-7115-407X"
TEST_RESEARCHER_NAME = "John Smith"
TEST_NIH_RECIPIENT_ORGANIZATION = "Harvard University"
TEST_NIH_GRANT_ID = "R01GM123456"
TEST_EPMC_QUERY = f'AUTHORID:"{TEST_ORCID_ID}"'

# Collections of identifiers for sample generation
SAMPLE_ORCID_IDS = [
    "0000-0002-7115-407X",
    "0000-0003-1527-0030",
    "0000-0001-8352-7209",
    "0000-0002-1825-0097",
    "0000-0001-5109-3700",
]

SAMPLE_RESEARCHER_NAMES = [
    "John Smith",
    "Jane Doe",
    "Robert Johnson",
    "Maria Garcia",
    "David Chen",
]

SAMPLE_NIH_RECIPIENT_ORGANIZATIONS = [
    "Harvard University",
    "Stanford University",
    "MIT",
    "University of California Berkeley",
    "Johns Hopkins University",
]

SAMPLE_NIH_GRANT_IDS = [
    "R01GM123456",
    "R21AI789012",
    "R01CA654321",
    "R01NS112233",
    "R01HL445566",
]

SAMPLE_EPMC_QUERIES = [f'AUTHORID:"{orcid}"' for orcid in SAMPLE_ORCID_IDS]
