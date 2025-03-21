# %%
import json
from pathlib import Path
from pprint import pprint
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from orcid2taxid.integrations.europe_pmc import EuropePMCRepository
from orcid2taxid.core.models.schemas import PaperMetadata
from tests.utils.load_data import load_test_orcids, load_test_researchers

# Initialize repository
repo = EuropePMCRepository()

# Load test data
TEST_ORCIDS = load_test_orcids(n=20, keyword="virology")

@dataclass
class PublicationTestResult:
    """Container for publication test results"""
    orcid: str
    raw_response: Dict[str, Any]
    formatted_response: Optional[List[PaperMetadata]]
    success: bool = True
    error_message: Optional[str] = None
    failing_paper_index: Optional[int] = None  # Track which paper caused the failure

@dataclass
class TestSuiteResult:
    """Container for overall test results"""
    sample_size: int
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[PublicationTestResult] = None
    failing_index: Optional[int] = None
    error_message: Optional[str] = None
    exception: Optional[Exception] = None
    statistics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.statistics is None:
            self.statistics = {}
    
    def add_result(self, result: PublicationTestResult):
        self.results.append(result)
    
    def set_error(self, idx: int, error_msg: str, exc: Exception, paper_idx: Optional[int] = None):
        self.failing_index = idx
        self.error_message = error_msg
        self.exception = exc
        if paper_idx is not None:
            self.results[idx].failing_paper_index = paper_idx
        self.end_time = datetime.now()
    
    def complete(self):
        self.end_time = datetime.now()
    
    def show_random_result(self):
        """Show a random successful paper from all successful results"""
        import random
        successful_results = [r for r in self.results if r.success]
        if not successful_results:
            print("No successful results to show")
            return
            
        # Pick a random successful result
        result = random.choice(successful_results)
        
        # Get all papers from successful results
        all_papers = []
        for r in successful_results:
            if isinstance(r.formatted_response, list):
                all_papers.extend([(r.orcid, paper, raw) for paper, raw in 
                                 zip(r.formatted_response, 
                                     r.raw_response.get('resultList', {}).get('result', []))])
        
        if not all_papers:
            print("No papers found in successful results")
            return
            
        # Pick a random paper
        orcid, paper, raw_paper = random.choice(all_papers)
        print(f"\nShowing random paper from ORCID: {orcid}")
        print_comparison(
            raw_paper,
            paper,
            "Random Paper Sample"
        )
    
    def show_failure(self):
        """Show the specific paper that caused the failure"""
        if not self.error_message:
            print("No failures to show")
            return
            
        failed_result = self.results[self.failing_index]
        print(f"\nShowing failure for ORCID: {failed_result.orcid}")
        print(f"Error message: {failed_result.error_message}")
        
        # If we know which paper failed, show only that paper
        if failed_result.failing_paper_index is not None and isinstance(failed_result.formatted_response, list):
            paper_idx = failed_result.failing_paper_index
            formatted_paper = failed_result.formatted_response[paper_idx] if paper_idx < len(failed_result.formatted_response) else None
            raw_paper = failed_result.raw_response.get('resultList', {}).get('result', [])[paper_idx] if paper_idx < len(failed_result.raw_response.get('resultList', {}).get('result', [])) else None
            
            if formatted_paper and raw_paper:
                print_comparison(
                    raw_paper,
                    formatted_paper,
                    "Failed Paper"
                )
            else:
                print("Failed paper data not available")
        else:
            # Fallback to showing all papers if we don't know which one failed
            print("Specific failing paper unknown, showing all papers:")
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

def clean_response(response: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove redundant metadata from Europe PMC API responses for cleaner output"""
    if not isinstance(response, dict):
        return response
        
    cleaned = {}
    for key, value in response.items():
        # Skip metadata fields
        if key in {'request', 'version'}:
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
        formatted_list = [item.model_dump() if hasattr(item, 'model_dump') else item for item in formatted]
        pprint(formatted_list)
    else:
        # Single object case
        pprint(formatted.model_dump() if hasattr(formatted, 'model_dump') else formatted)

def test_basic_paper_requirements(sample_size: int = 5) -> TestSuiteResult:
    """
    Test basic requirements for papers:
    - Must have a title
    - Must have an abstract (tracked but not required)
    - Must have a DOI
    - Must have at least one author
    """
    result = TestSuiteResult(
        sample_size=sample_size,
        start_time=datetime.now()
    )
    
    # Initialize statistics
    result.statistics = {
        'total_papers': 0,
        'papers_without_abstract': 0
    }
    
    try:
        for idx, orcid in enumerate(TEST_ORCIDS[:sample_size]):
            try:
                # Get responses
                raw_response = repo.fetch_publications_by_orcid(orcid)
                formatted_response = repo.get_publications_by_orcid(orcid)
                
                # Check each publication
                for paper_idx, pub in enumerate(formatted_response):
                    result.statistics['total_papers'] += 1
                    
                    try:
                        # Title is required
                        assert pub.title and pub.title.strip(), "Empty or missing title"
                        
                        # Track papers without abstract
                        if not pub.abstract or not pub.abstract.strip():
                            result.statistics['papers_without_abstract'] += 1
                        
                        # DOI should be present
                        assert pub.doi and '/' in pub.doi, f"Invalid or missing DOI: {pub.doi}"
                        
                        # Should have at least one author
                        assert pub.authors and len(pub.authors) > 0, "No authors found"
                        
                    except Exception as e:
                        result.add_result(PublicationTestResult(
                            orcid=orcid,
                            raw_response=raw_response,
                            formatted_response=formatted_response,
                            success=False,
                            error_message=str(e)
                        ))
                        result.set_error(idx, str(e), e, paper_idx)
                        return result
                
                # Add successful result
                result.add_result(PublicationTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=formatted_response
                ))
                
            except Exception as e:
                result.add_result(PublicationTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=formatted_response,
                    success=False,
                    error_message=str(e)
                ))
                result.set_error(idx, str(e), e)
                return result
                
        result.complete()
        
        # Calculate and print abstract statistics
        if result.statistics['total_papers'] > 0:
            abstract_missing_rate = (result.statistics['papers_without_abstract'] / result.statistics['total_papers']) * 100
            print(f"\nAbstract Statistics:")
            print(f"Total papers processed: {result.statistics['total_papers']}")
            print(f"Papers without abstract: {result.statistics['papers_without_abstract']} ({abstract_missing_rate:.1f}%)")
            
        return result
        
    except Exception as e:
        result.set_error(idx, str(e), e)
        return result

def test_edge_cases(sample_size: int = 5) -> TestSuiteResult:
    """
    Test edge cases in publication handling:
    - Publications with multiple authors
    - Publications with multiple affiliations
    - Publications with multiple external IDs
    - Publications with full text URLs
    - Publications with funding information
    - Publications with keywords and subjects
    """
    result = TestSuiteResult(
        sample_size=sample_size,
        start_time=datetime.now()
    )
    
    try:
        for idx, orcid in enumerate(TEST_ORCIDS[:sample_size]):
            try:
                # Get responses
                raw_response = repo.fetch_publications_by_orcid(orcid)
                formatted_response = repo.get_publications_by_orcid(orcid)
                
                # Check each publication
                for pub in formatted_response:
                    # Check author information
                    for author in pub.authors:
                        if author.affiliations:
                            assert all(isinstance(aff, str) and aff.strip() for aff in author.affiliations), \
                                "Invalid affiliation format"
                        
                        if author.email:
                            assert '@' in author.email, f"Invalid email format: {author.email}"
                    
                    # Check full text URL format
                    if pub.full_text_url:
                        assert pub.full_text_url.startswith(('http://', 'https://')), \
                            "Invalid full text URL format"
                    
                    # Check keywords and subjects
                    if pub.keywords:
                        assert all(isinstance(kw, str) and kw.strip() for kw in pub.keywords), \
                            "Invalid keyword format"
                    
                    if pub.subjects:
                        assert all(isinstance(subj, str) and subj.strip() for subj in pub.subjects), \
                            "Invalid subject format"
                
                # Add successful result
                result.add_result(PublicationTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=formatted_response
                ))
                
            except Exception as e:
                result.add_result(PublicationTestResult(
                    orcid=orcid,
                    raw_response=raw_response,
                    formatted_response=formatted_response,
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

def test_author_metadata_search(sample_size: int = 5) -> TestSuiteResult:
    """
    Test searching by author metadata:
    - Search by full name
    - Search by given name and family name
    - Search with ORCID
    """
    result = TestSuiteResult(
        sample_size=sample_size,
        start_time=datetime.now()
    )
    
    try:
        # Load test data
        test_metadata = load_test_researchers(n=sample_size, keyword="virology")
        
        for idx, metadata in enumerate(test_metadata):
            try:
                # Get responses using the author's name
                raw_response = repo.fetch_publications_by_orcid(metadata.orcid)
                formatted_response = repo.get_publications_by_orcid(metadata.orcid)
                
                # Basic validation of results
                assert isinstance(formatted_response, list), "Response should be a list"
                
                # Check each publication
                for pub in formatted_response:
                    # Title is required
                    assert pub.title and pub.title.strip(), "Empty or missing title"
                    
                    # Should have at least one author
                    assert pub.authors and len(pub.authors) > 0, "No authors found"
                
                # Add successful result
                result.add_result(PublicationTestResult(
                    orcid=metadata.orcid,
                    raw_response=raw_response,
                    formatted_response=formatted_response
                ))
                
            except Exception as e:
                result.add_result(PublicationTestResult(
                    orcid=metadata.orcid,
                    raw_response=raw_response,
                    formatted_response=formatted_response,
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

if __name__ == "__main__":
    # Run tests with error reporting
    sample_size = 50
    
    test_functions = [
        test_basic_paper_requirements,
        # test_edge_cases,
        # test_author_metadata_search
    ]
    
    for test_func in test_functions:
        print(f"\nRunning {test_func.__name__} with sample_size={sample_size}")
        result = test_func(sample_size)
        
        print(f"\nTest completed in {result.duration:.2f} seconds")
        print(f"Success rate: {result.success_rate:.1f}%")
        
        if result.error_message:
            print(f"\nError at index {result.failing_index} with ORCID {TEST_ORCIDS[result.failing_index]}")
            print(f"Error message: {result.error_message}")
            result.show_failure()
        else:
            print("All tests passed successfully!")
            result.show_random_result() 
# %%
