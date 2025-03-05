# %%
import logging
from orcid2taxid.data.clients.taxid_client import NCBITaxIDLookup
from orcid2taxid.analysis.text.text_analysis_service import LLMAnalyzer
from orcid2taxid.core.models.schemas import PaperMetadata
from tests.utils.load_data import load_test_abstracts

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# Filter out httpx HTTP request logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize clients
analyzer = LLMAnalyzer()
taxid_lookup = NCBITaxIDLookup()


# Test full pipeline
def test_pipeline(n: int = 1):
    abstracts_data = load_test_abstracts(n)
    
    for orcid_data in abstracts_data:
        for paper in orcid_data['abstracts']:
            logger.info(f"\nPaper: {paper['title']}")
            
            paper_metadata = PaperMetadata(
                title=paper['title'],
                abstract=paper['abstract'],
                doi=paper['doi'],
                pmid=paper['pmid']
            )
            
            organisms = analyzer.extract_organisms_from_abstract(paper_metadata)
            for org in organisms:
                logger.info(f"\nFound: {org.original_name}")
                taxonomy = taxid_lookup.get_taxid(org.searchable_name)
                if taxonomy:
                    logger.info(f"TAXID: {taxonomy.taxid}")
                    logger.info(f"Scientific name: {taxonomy.scientific_name}")
                else:
                    logger.warning(f"No taxonomy found for: {org.searchable_name}")

if __name__ == "__main__":
    # Uncomment the test you want to run
    # test_single_taxid()
    # test_single_paper()
    test_pipeline(n=10)
