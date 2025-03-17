from orcid2taxid.data.clients.orcid_client import OrcidClient
from orcid2taxid.data.repositories.europe_pmc import EuropePMCRepository
from orcid2taxid.analysis.text.organism_extractor import LLMOrganismExtractor
from orcid2taxid.data.clients.taxid_client import NCBITaxIDLookup
from orcid2taxid.core.models.schemas import (
    OrganismMention, 
    OrganismList
)
import argparse
import logging
from typing import List

def main() -> List[OrganismList]:
    # Set up logging and parse arguments
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Convert ORCID to associated TAXIDs')
    parser.add_argument('orcid', help='ORCID ID of the researcher')
    args = parser.parse_args()

    # Initialize components
    orcid_client = OrcidClient()
    repositories = [EuropePMCRepository()]
    text_analysis_service = LLMOrganismExtractor()
    taxonomy_repository = NCBITaxIDLookup()

    # 1. Get author information from ORCID
    author_metadata = orcid_client.get_researcher_info(args.orcid)
    orcid_papers = orcid_client.get_publications_by_orcid(args.orcid)

    # 2. Get publications from different sources
    papers = [paper for repo in repositories for paper in repo.search_publications(args.orcid, author_metadata)]

    # 3. Process each paper to find organisms
    results = []
    for paper in papers:
        organisms = set()
        
        # If no full text, fall back to abstract
        llm_names = text_analysis_service.analyze_text_for_organisms(paper['abstract'])
        refined_names = text_analysis_service.standardize_names_for_ncbi_search(llm_names)
        organisms.update(refined_names)

        # 4. Map organisms to TAXIDs
        taxids = {}
        for organism in organisms:
            taxid = taxonomy_repository.get_taxid(organism)
            if taxid:
                taxids[organism] = taxid

        organism_mentions = [
            OrganismMention(
                name=organism,
                confidence_score=1.0,
                source="llm",
                context=None  # Add context if available
            )
            for organism in organisms
        ]
        
        results.append(OrganismList(
            paper_id=paper.get('doi') or paper.get('id'),
            organisms=organism_mentions,
            taxids={org.name: taxid for org, taxid in zip(organism_mentions, taxids)},
            extraction_method="full_text" if paper.get('full_text') else "abstract_only"
        ))

    # 5. Output results
    logging.info(f"Found {len(results)} papers with {len(set().union(*[r['taxids'].values() for r in results]))} unique TAXIDs")
    return results

if __name__ == "__main__":
    main()