from orcid2taxid.data.clients.orcid_client import OrcidClient
from orcid2taxid.data.repositories.biorxiv import BiorxivRepository
from orcid2taxid.data.repositories.europe_pmc import EuropePMCRepository
from orcid2taxid.data.clients.unpaywall_client import UnpaywallFetcher
from orcid2taxid.analysis.filtering.authorship_filter import AuthorshipVerificationFilter
from orcid2taxid.analysis.filtering.duplicate_filter import DuplicatePublicationFilter
from orcid2taxid.analysis.detection.organism_detector import GnfFinder
from orcid2taxid.analysis.text.text_analysis_service import LLMAnalyzer
from orcid2taxid.data.clients.taxid_client import NCBITaxIDLookup
from orcid2taxid.core.models.schemas import (
    AuthorMetadata, 
    PaperMetadata, 
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
    repositories = [EuropePMCRepository(), BiorxivRepository()]
    unpaywall_repository = UnpaywallFetcher(email="your@email.com")  # Replace with config
    organism_detector = GnfFinder(gnf_api_url="https://gnf.globalnames.org/api/v1")
    text_analysis_service = LLMAnalyzer(model_name="claude-3-5-haiku-20240307")
    taxonomy_repository = NCBITaxIDLookup()

    # 1. Get author information from ORCID
    author_metadata = orcid_client.fetch_researcher_info(args.orcid)
    orcid_papers = orcid_client.fetch_publications(args.orcid)

    # 2. Get publications from different sources
    papers = [paper for repo in repositories for paper in repo.search_publications(args.orcid, author_metadata)]

    # 2. Filter and deduplicate papers
    duplicate_filter = DuplicatePublicationFilter()
    unique_papers = duplicate_filter.remove_duplicates(papers)
    
    author_filter = AuthorshipVerificationFilter(known_papers=orcid_papers)
    verified_papers = [
        paper for paper, score in author_filter.verify_authorship(unique_papers).items()
        if score >= 0.8  # Using default threshold
    ]

    # 3. Process each paper to find organisms
    results = []
    for paper in verified_papers:
        organisms = set()
        
        # Try to get full text first
        if 'doi' in paper:
            fulltext_info = unpaywall_repository.fetch_fulltext_url(paper['doi'])
            if fulltext_info.get('has_pdf'):
                pdf_path = f"temp/{paper['doi'].replace('/', '_')}.pdf"
                if unpaywall_repository.download_pdf(paper['doi'], pdf_path):
                    # Process full text with GNF first, then LLM
                    gnf_names = organism_detector.detect_organisms_in_file(pdf_path)
                    refined_names = text_analysis_service.standardize_names_for_ncbi_search(gnf_names)
                    organisms.update(refined_names)

        # If no full text, fall back to abstract
        if not organisms and 'abstract' in paper:
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
                source="gnf+llm" if paper.get('full_text') else "llm",
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