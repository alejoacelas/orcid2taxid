# %%
import logging
from orcid2taxid.integrations.ncbi_taxids import TaxIDLookup
from orcid2taxid.analysis.extraction.paper import PaperExtractor
from tests.utils.load_data import load_test_papers

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# Filter out httpx HTTP request logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize clients
analyzer = PaperExtractor()
taxid_lookup = TaxIDLookup()


# Test full pipeline
def test_pipeline(n: int = 1):
    papers_data = load_test_papers(n, keyword="virology")
    
    for paper in papers_data:
        logger.info(f"\nPaper: {paper.title}")
        organisms = analyzer.extract_organisms_from_abstract(paper)
        for org in organisms:
            logger.info(f"\nFound: {org.original_name}")
            taxonomy = taxid_lookup.get_taxid(org.searchable_name)
            if taxonomy:
                logger.info(f"TAXID: {taxonomy.taxid}")
                logger.info(f"Scientific name: {taxonomy.scientific_name}")
            else:
                logger.warning(f"No taxonomy found for: {org.searchable_name}")

if __name__ == "__main__":
    test_pipeline(n=10)

# %%
