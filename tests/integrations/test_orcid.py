# %%
from pprint import pprint
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from orcid2taxid.integrations.orcid import OrcidClient
from orcid2taxid.core.models.schemas import ResearcherMetadata, PaperMetadata
from tests.utils.load_data import load_test_orcids, load_test_researchers, load_test_papers

# Initialize client
client = OrcidClient()

# Load test data
TEST_ORCIDS = load_test_orcids(n=20, keyword="virology")

# %%
@dataclass
class AuthorTestResult:
    """Container for author metadata test results"""
    orcid: str
    raw_response: Dict[str, Any]
    formatted_response: Optional[ResearcherMetadata]
    success: bool = True
    error_message: Optional[str] = None
    
@dataclass
class PublicationTestResult:
    """Container for publication test results"""
    orcid: str
    raw_response: Dict[str, Any]
    formatted_response: Optional[List[PaperMetadata]]
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class TestSuiteResult:
    """Container for overall test results"""
    sample_size: int
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[AuthorTestResult | PublicationTestResult] = None
    failing_index: Optional[int] = None
    error_message: Optional[str] = None
    exception: Optional[Exception] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    def add_result(self, result: AuthorTestResult | PublicationTestResult):
        self.results.append(result)
    
    def set_error(self, idx: int, error_msg: str, exc: Exception):
        self.failing_index = idx
        self.error_message = error_msg
        self.exception = exc
        self.end_time = datetime.now()
    
    def complete(self):
        self.end_time = datetime.now()
    
    def show_random_result(self):
        """Show a random successful result with raw and formatted response comparison"""
        import random
        successful_results = [r for r in self.results if r.success]
        if not successful_results:
            print("No successful results to show")
            return
            
        result = random.choice(successful_results)
        print(f"\nShowing random result for ORCID: {result.orcid}")
        print_comparison(
            result.raw_response,
            result.formatted_response,
            "Random Sample"
        )
    
    def show_failure(self):
        """Show the failed result with raw and formatted response comparison"""
        if not self.error_message:
            print("No failures to show")
            return
            
        failed_result = self.results[self.failing_index]
        print(f"\nShowing failure for ORCID: {failed_result.orcid}")
        print(f"Error message: {failed_result.error_message}")
        print_comparison(
            failed_result.raw_response,
            failed_result.formatted_response,
            "Failed Sample"
        )
    
    @property
    def duration(self) -> float:
        """Return test duration in seconds"""
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Return percentage of successful tests"""
        if not self.results:
            return 0
        return sum(1 for r in self.results if r.success) / len(self.results) * 100

# Helper functions for cleaner output
def clean_response(response: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove redundant metadata from ORCID API responses for cleaner output"""
    if not isinstance(response, dict):
        return response
        
    cleaned = {}
    for key, value in response.items():
        # Skip path and other metadata
        if key in {'path', 'last-modified-date', 'created-date', 'source'}:
            continue
            
        if isinstance(value, dict):
            cleaned[key] = clean_response(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_response(item) for item in value]
        else:
            cleaned[key] = value
            
    return cleaned

def print_comparison(raw: Dict[Any, Any], formatted: Dict[Any, Any] | List[Any], title: str = ""):
    """Print raw and formatted responses side by side for comparison"""
    print(f"\n{'='*20} {title} {'='*20}")
    print("\nRaw Response (Cleaned):")
    pprint(clean_response(raw))
    print("\nFormatted Response:")
    if isinstance(formatted, list):
        # If it's a list, convert each item to dict if possible
        formatted_list = [item.dict() if hasattr(item, 'dict') else item for item in formatted]
        pprint(formatted_list)
    else:
        # Single object case
        pprint(formatted.dict() if hasattr(formatted, 'dict') else formatted)

# %%
def test_name_edge_cases(sample_size: int = 5) -> TestSuiteResult:
    """
    Test edge cases in name handling:
    - Missing given/family names
    - Only credit name present
    - Unicode characters
    - Empty name fields
    """
    result = TestSuiteResult(
        sample_size=sample_size,
        start_time=datetime.now()
    )
    idx = 0  # Initialize idx
    
    try:
        # Load test data
        test_orcids = load_test_orcids(n=sample_size, keyword="virology")
        test_metadata = load_test_researchers(n=sample_size, keyword="virology")
        
        for idx, (orcid, metadata) in enumerate(zip(test_orcids, test_metadata)):
            try:
                # Get raw response for comparison
                raw_response = client.fetch_author_metadata(orcid)
                
                # Validate name handling
                assert metadata.full_name, "Missing required field: full_name"
                if not metadata.given_name and not metadata.family_name:
                    assert metadata.credit_name or metadata.full_name != "Unknown", \
                        "No name information available"
                
                # Check name field consistency
                if metadata.given_name or metadata.family_name:
                    expected_full = f"{metadata.family_name or ''}, {metadata.given_name or ''}".strip(', ')
                    assert metadata.full_name == expected_full, \
                        f"Full name {metadata.full_name} doesn't match components: {expected_full}"
                
                # Add successful result
                result.add_result(AuthorTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=metadata
                ))
                
            except Exception as e:
                result.add_result(AuthorTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=metadata,
                    success=False,
                    error_message=str(e)
                ))
                result.set_error(idx, str(e), e)
                return result
                
        result.complete()
        return result
        
    except Exception as e:
        result.set_error(idx, str(e), e)
        return result

def test_affiliation_edge_cases(sample_size: int = 5) -> TestSuiteResult:
    """
    Test edge cases in affiliation handling:
    - Missing institution names
    - Invalid dates
    - Partial dates
    - Future dates
    - Empty but present fields
    """
    result = TestSuiteResult(
        sample_size=sample_size,
        start_time=datetime.now()
    )
    idx = 0  # Initialize idx
    
    try:
        # Load test data
        test_orcids = load_test_orcids(n=sample_size, keyword="virology")
        test_metadata = load_test_researchers(n=sample_size, keyword="virology")
        
        for idx, (orcid, metadata) in enumerate(zip(test_orcids, test_metadata)):
            try:
                # Get raw response for comparison
                raw_response = client.fetch_author_metadata(orcid)
                
                # Check education entries
                for edu in metadata.education:
                    assert edu.institution_name and edu.institution_name.strip(), \
                        "Empty or missing institution name in education"
                    
                    # Validate dates if present
                    if edu.start_date and edu.end_date:
                        start = datetime.strptime(edu.start_date, "%Y-%m-%d")
                        end = datetime.strptime(edu.end_date, "%Y-%m-%d")
                        assert start <= end, f"Invalid date range: {edu.start_date} to {edu.end_date}"
                        
                        # Check for future dates
                        now = datetime.now()
                        if end > now:
                            print(f"Warning: Future end date found: {edu.end_date}")
                
                # Check employment entries
                for aff in metadata.affiliations:
                    assert aff.institution_name and aff.institution_name.strip(), \
                        "Empty or missing institution name in affiliation"
                    
                    # Validate dates if present
                    if aff.start_date and aff.end_date:
                        start = datetime.strptime(aff.start_date, "%Y-%m-%d")
                        end = datetime.strptime(aff.end_date, "%Y-%m-%d")
                        assert start <= end, f"Invalid date range: {aff.start_date} to {aff.end_date}"
                
                # Add successful result
                result.add_result(AuthorTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=metadata
                ))
                
            except Exception as e:
                result.add_result(AuthorTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=metadata,
                    success=False,
                    error_message=str(e)
                ))
                result.set_error(idx, str(e), e)
                return result
                
        result.complete()
        return result
        
    except Exception as e:
        result.set_error(idx, str(e), e)
        return result

def test_publication_edge_cases(sample_size: int = 1) -> TestSuiteResult:
    """
    Test edge cases in publication handling:
    - Missing titles
    - Invalid dates
    - Multiple DOIs
    - Empty work groups
    - Missing preferred work version
    """
    result = TestSuiteResult(
        sample_size=sample_size,
        start_time=datetime.now()
    )
    idx = 0  # Initialize idx
    
    try:
        # Load test data
        test_orcids = load_test_orcids(n=sample_size, keyword="virology")
        test_papers = load_test_papers(n=sample_size, keyword="virology")
        
        for idx, (orcid, papers) in enumerate(zip(test_orcids, test_papers)):
            try:
                # Get raw response for comparison
                raw_response = client.fetch_publications_by_orcid(orcid)
                
                # Check each publication
                for pub in papers:
                    # Title is required
                    assert pub.title and pub.title.strip(), "Empty or missing title"
                    
                    # Check publication date format if present
                    if pub.publication_date:
                        try:
                            datetime.strptime(pub.publication_date, "%Y-%m-%d")
                        except ValueError:
                            raise AssertionError(f"Invalid publication date format: {pub.publication_date}")
                    
                    # Check DOI format if present
                    if pub.doi:
                        assert '/' in pub.doi, f"Invalid DOI format: {pub.doi}"
                    
                    # Validate URLs if present
                    if pub.full_text_url:
                        assert pub.full_text_url.startswith(('http://', 'https://')), \
                            f"Invalid URL format: {pub.full_text_url}"
                
                # Add successful result
                result.add_result(PublicationTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=papers
                ))
                
            except Exception as e:
                result.add_result(PublicationTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=papers,
                    success=False,
                    error_message=str(e)
                ))
                result.set_error(idx, str(e), e)
                return result
                
        result.complete()
        return result
        
    except Exception as e:
        result.set_error(idx, str(e), e)
        return result

def test_error_logging(sample_size: int = 5) -> TestSuiteResult:
    """
    Test error and warning logging in the ORCID client.
    This test specifically checks:
    - Critical errors that stop processing
    - Warning conditions that allow processing to continue
    - Proper error flag setting
    """
    result = TestSuiteResult(
        sample_size=sample_size,
        start_time=datetime.now()
    )
    idx = 0  # Initialize idx
    
    try:
        # Load test data
        test_orcids = load_test_orcids(n=sample_size, keyword="virology")
        test_metadata = load_test_researchers(n=sample_size, keyword="virology")
        test_papers = load_test_papers(n=sample_size, keyword="virology")
        
        for idx, (orcid, metadata, papers) in enumerate(zip(test_orcids, test_metadata, test_papers)):
            try:
                # Create a new client instance for each test to ensure clean error state
                client = OrcidClient()
                
                # Test author metadata retrieval
                author_data = client.get_author_metadata(orcid)
                if client.error_occurred:
                    raise Exception(f"Critical error occurred while fetching author metadata for ORCID {orcid}")
                
                # Test publication retrieval
                publications = client.get_publications_by_orcid(orcid)
                if client.error_occurred:
                    raise Exception(f"Critical error occurred while fetching publications for ORCID {orcid}")
                
                # Add successful result
                result.add_result(AuthorTestResult(
                    orcid=orcid,
                    raw_response={'author': metadata.dict(), 'publications': [p.dict() for p in papers]},
                    formatted_response=author_data,
                    success=True
                ))
                
            except Exception as e:
                result.add_result(AuthorTestResult(
                    orcid=orcid,
                    raw_response={},
                    formatted_response=None,
                    success=False,
                    error_message=str(e)
                ))
                result.set_error(idx, str(e), e)
                return result
                
        result.complete()
        return result
        
    except Exception as e:
        result.set_error(idx, str(e), e)
        return result

# %%
# Run tests with error reporting
sample_size = 5
# test_func = test_affiliation_edge_cases
test_func = test_name_edge_cases
# test_func = test_publication_edge_cases
# test_func = test_error_logging

print(f"\nRunning {test_func.__name__} with sample_size={sample_size}")
result = test_func(sample_size)

print(f"\nTest completed in {result.duration:.2f} seconds")
print(f"Success rate: {result.success_rate:.1f}%")

if result.error_message:
    print(f"\nError at index {result.failing_index} with ORCID {TEST_ORCIDS[result.failing_index]}")
    print(f"Error message: {result.error_message}")
    raise result.exception
else:
    print("All tests passed successfully!")
        
# %%

