from orcid.orcid import OrcidFetcher
from publications.repositories.pubmed import PubmedFetcher
from publications.repositories.biorxiv import BiorxivFetcher
from publications.tools.unpaywall import UnpaywallFetcher
from filters.author_verification import AuthorVerificationFilter
from filters.duplicate_publications import DuplicateFilter
from text_analysis.gnf_finder import GnfFinder
from text_analysis.llm_analyzer import LLMAnalyzer
from taxid.ncbi_taxid_lookup import NCBITaxIDLookup
from schemas.schemas import (
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
    orcid_fetcher = OrcidFetcher()
    repositories = [PubmedFetcher(), BiorxivFetcher()]
    unpaywall = UnpaywallFetcher(email="your@email.com")  # Replace with config
    gnf_finder = GnfFinder(gnf_api_url="https://gnf.globalnames.org/api/v1")
    llm_analyzer = LLMAnalyzer(model_name="claude-3-5-haiku-20240307")
    taxid_lookup = NCBITaxIDLookup()


    # 1. Get author information from ORCID
    author_metadata = orcid_fetcher.fetch_researcher_info(args.orcid)
    orcid_papers = orcid_fetcher.fetch_publications(args.orcid)

    # 2. Get publications from different sources
    papers = [paper for repo in repositories for paper in repo.search_publications(args.orcid, author_metadata)]

    # 2. Filter and deduplicate papers
    duplicate_filter = DuplicateFilter()
    unique_papers = duplicate_filter.remove_duplicates(papers)
    
    author_filter = AuthorVerificationFilter(known_papers=orcid_papers)
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
            fulltext_info = unpaywall.fetch_fulltext_link(paper['doi'])
            if fulltext_info.get('has_pdf'):
                pdf_path = f"temp/{paper['doi'].replace('/', '_')}.pdf"
                if unpaywall.download_pdf(paper['doi'], pdf_path):
                    # Process full text with GNF first, then LLM
                    gnf_names = gnf_finder.find_names_in_file(pdf_path)
                    refined_names = llm_analyzer.standardize_names_for_ncbi_search(gnf_names)
                    organisms.update(refined_names)

        # If no full text, fall back to abstract
        if not organisms and 'abstract' in paper:
            llm_names = llm_analyzer.analyze_text_for_organisms(paper['abstract'])
            refined_names = llm_analyzer.standardize_names_for_ncbi_search(llm_names)
            organisms.update(refined_names)

        # 4. Map organisms to TAXIDs
        taxids = {}
        for organism in organisms:
            taxid = taxid_lookup.get_taxid(organism)
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