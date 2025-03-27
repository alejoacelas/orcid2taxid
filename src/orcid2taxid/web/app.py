import streamlit as st
import asyncio
from orcid2taxid.integrations.europe_pmc import EuropePMCRepository
from orcid2taxid.analysis.extraction.paper import PaperExtractor
from orcid2taxid.integrations.ncbi import TaxIDLookup
from orcid2taxid.core.operations.researcher import get_researcher_by_orcid, find_publications
from orcid2taxid.core.operations.paper import get_classification, get_organisms, get_taxonomy_info, process_paper_async
from orcid2taxid.core.operations.grant import find_grants
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from orcid2taxid.core.models.schemas import PaperMetadata, OrganismMention, ResearcherMetadata, GrantMetadata

# Custom hash functions for Pydantic models
def hash_paper_metadata(paper: PaperMetadata) -> tuple:
    """Create a hashable tuple from essential paper fields"""
    return (
        paper.title,
        paper.abstract,
        paper.doi,
        paper.publication_date,
        paper.journal_name,  # Added to improve uniqueness
        # Include a hash of authors' names if available
        tuple(author.full_name for author in paper.authors) if paper.authors else None
    )

def hash_grant_metadata(grant: GrantMetadata) -> tuple:
    """Create a hashable tuple from essential grant fields"""
    return (
        grant.project_title,
        grant.project_num,
        grant.funder,
        grant.pi_name,  # Added to improve uniqueness
        grant.project_start_date  # Added to distinguish between versions of the same grant
    )

def hash_researcher_metadata(researcher: ResearcherMetadata) -> tuple:
    """Create a hashable tuple from essential researcher fields"""
    return (
        researcher.orcid,
        researcher.full_name,
        researcher.given_name,
        researcher.family_name,
        researcher.last_modified,  # Added to detect updates to the profile
        len(researcher.publications)  # Added to detect when publications have been added
    )

@st.cache_data()
def fetch_researcher_by_orcid(orcid: str) -> ResearcherMetadata:
    """Cached function to fetch basic researcher metadata"""
    return get_researcher_by_orcid(orcid)

@st.cache_data(hash_funcs={ResearcherMetadata: hash_researcher_metadata})
def fetch_publications(researcher: ResearcherMetadata) -> ResearcherMetadata:
    """Cached function to fetch publications for a researcher
    
    Uses underscore prefix to prevent Streamlit from hashing the researcher object"""
    return find_publications(researcher, max_results=50)

@st.cache_data(hash_funcs={ResearcherMetadata: hash_researcher_metadata})
def fetch_grants(researcher: ResearcherMetadata) -> ResearcherMetadata:
    """Cached function to fetch grants for a researcher
    
    Uses underscore prefix to prevent Streamlit from hashing the researcher object"""
    return find_grants(researcher)

@st.cache_data(hash_funcs={PaperMetadata: hash_paper_metadata})
def extract_organisms_from_paper(paper: PaperMetadata) -> PaperMetadata:
    """Cached function to extract organisms from a paper
    
    Uses underscore prefix to prevent Streamlit from hashing the paper object"""
    return get_organisms(paper)

@st.cache_data(hash_funcs={PaperMetadata: hash_paper_metadata})
def classify_paper(paper: PaperMetadata) -> PaperMetadata:
    """Cached function to classify a paper
    
    Uses underscore prefix to prevent Streamlit from hashing the paper object"""
    return get_classification(paper)

@st.cache_data(hash_funcs={PaperMetadata: hash_paper_metadata})
def get_taxonomy(paper: PaperMetadata) -> PaperMetadata:
    """Cached function to get taxonomy info for a paper
    
    Uses underscore prefix to prevent Streamlit from hashing the paper object"""
    return get_taxonomy_info(paper)

# IMPORTANT: Do NOT cache async functions directly with st.cache_data
# Instead, we'll create a sync function for caching results after processing

# We'll maintain a simple in-memory cache for processed papers
_paper_cache = {}

async def process_paper_async_wrapper(paper: PaperMetadata) -> PaperMetadata:
    """Async wrapper for processing a paper that checks an in-memory cache first"""
    # Create a cache key using the hash_paper_metadata function
    cache_key = hash_paper_metadata(paper)
    
    # Check if we already processed this paper
    if cache_key in _paper_cache:
        return _paper_cache[cache_key]
    
    # Process the paper
    processed_paper = await process_paper_async(paper)
    
    # Cache the result
    _paper_cache[cache_key] = processed_paper
    
    return processed_paper

def process_single_paper(researcher: ResearcherMetadata, paper_index: int, taxid_client: TaxIDLookup) -> ResearcherMetadata:
    """Process a single paper and update the researcher object
    
    This function updates the researcher's publication at the specified index with:
    1. Extracted organisms
    2. Classification information
    3. Taxonomy information
    
    Returns the updated researcher object
    """
    if paper_index >= len(researcher.publications):
        return researcher
        
    # Get the paper to process
    paper = researcher.publications[paper_index]
    
    # Extract organisms and classify paper
    updated_paper = extract_organisms_from_paper(paper)
    updated_paper = classify_paper(updated_paper)
    
    # Process organisms and taxonomy
    for organism in updated_paper.organisms:
        if not organism.taxonomy_info:  # Only get taxonomy info if not already present
            tax_info = taxid_client.get_taxid(organism.searchable_name)
            if tax_info:
                organism.taxonomy_info = tax_info
    
    # Update the paper in the researcher object
    researcher.publications[paper_index] = updated_paper
    return researcher

async def process_papers_in_batch(researcher: ResearcherMetadata, batch_size: int = 10) -> ResearcherMetadata:
    """Process papers in batches asynchronously
    
    This function processes papers in batches to respect rate limits while
    maximizing concurrency. Each batch is processed in parallel.
    
    Returns the updated researcher object
    """
    if not researcher.publications:
        return researcher
        
    # Process papers in batches
    for i in range(0, len(researcher.publications), batch_size):
        batch = researcher.publications[i:i+batch_size]
        
        # Process batch asynchronously
        tasks = [process_paper_async_wrapper(paper) for paper in batch]
        processed_papers = await asyncio.gather(*tasks)
        
        # Update papers in researcher object
        for j, processed_paper in enumerate(processed_papers):
            researcher.publications[i+j] = processed_paper
            
        # Update progress
        st.session_state.current_paper_index = i + len(batch)
        
    return researcher

def display_researcher_info(researcher: ResearcherMetadata):
    """Display researcher information"""
    st.subheader("Researcher Profile")
    full_name = f"{researcher.given_name} {researcher.family_name}"
    st.markdown(f"**Name:** {full_name}")
    
    # Display affiliations
    st.markdown("#### Employment History")
    if researcher.affiliations:
        for affiliation in researcher.affiliations:
            st.markdown(f"- {affiliation.institution_name}" + 
                        (f", {affiliation.department}" if affiliation.department else ""))
    else:
        st.info("No employment history found on their ORCID profile.")
    
    # Display education
    st.markdown("#### Education")
    if researcher.education:
        for education in researcher.education:
            st.markdown(f"- {education.institution_name}" + 
                        (f", {education.department}" if education.department else ""))
    else:
        st.info("No education history found on their ORCID profile.")

def display_highlights(researcher: ResearcherMetadata):
    """Display paper highlights from the researcher's publications"""
    processed_papers = [p for p in researcher.publications if p.classification]
    has_highlights = False
    
    for paper in processed_papers:
        # Check for specific highlights
        if paper.classification.wet_lab_work == "yes":
            st.warning(f"⚗️ Wet lab work detected in paper: \"{paper.title}\"")
            has_highlights = True
        
        if paper.classification.bsl_level in ["bsl_2", "bsl_3", "bsl_4"]:
            st.error(f"🧪 {paper.classification.bsl_level.upper()} lab work detected in paper: \"{paper.title}\"")
            has_highlights = True
        
        if "vaccine_development" in paper.classification.dna_use:
            st.success(f"💉 Vaccine development work detected in paper: \"{paper.title}\"")
            has_highlights = True
        
        if "synthetic_genome" in paper.classification.dna_type:
            st.warning(f"🧬 Synthetic genome work detected in paper: \"{paper.title}\"")
            has_highlights = True
    
    if not has_highlights and processed_papers:
        st.info("No highlights detected in the analyzed papers.")
    elif not processed_papers:
        st.info("No papers have been analyzed yet.")

def display_organisms(researcher: ResearcherMetadata):
    """Display organisms from the researcher's publications"""
    organism_to_papers = researcher.get_publications_by_organism()
    
    if organism_to_papers:
        for scientific_name, papers_list in organism_to_papers.items():
            # Get the first paper's organism to access taxonomy info
            first_paper = papers_list[0]
            organism = next(o for o in first_paper.organisms if o.taxonomy_info and o.taxonomy_info.scientific_name == scientific_name)
            taxid = organism.taxonomy_info.taxid
            
            # Create help text with context and paper links
            help_text = []
            for paper in papers_list:
                # Find the organism mention in this paper
                paper_organism = next(o for o in paper.organisms if o.taxonomy_info and o.taxonomy_info.scientific_name == scientific_name)
                context = f'"{paper_organism.context}"' if paper_organism.context else "No context available"
                
                # Create paper link if DOI is available
                paper_link = f"[(link)](https://doi.org/{paper.doi})" if paper.doi else paper.title
                help_text.append(f"* {context} {paper_link}")
            
            taxid_link = f"[TaxID {taxid}](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={taxid})"
            st.markdown(f"- **{scientific_name.capitalize()}** ({taxid_link})", help="\n\n".join(help_text))
    else:
        st.info("No organisms identified yet.")

def display_papers(researcher: ResearcherMetadata):
    """Display paper list from the researcher's publications"""
    
    processed_papers = [p for p in researcher.publications if p.classification]
    
    if processed_papers:
        for paper in processed_papers:
            if paper.doi:
                st.markdown(f"- [{paper.title}](https://doi.org/{paper.doi})")
            else:
                st.markdown(f"- {paper.title}")
    else:
        st.info("No processed publications yet.")

def display_grants(researcher: ResearcherMetadata):
    """Display grant information from the researcher's grants"""
    if researcher.grants:
        for grant in researcher.grants:
            with st.expander(f"{grant.project_title[:100]}..."):
                st.markdown(f"**Project Number**: {grant.project_num}")
                if grant.funder:
                    st.markdown(f"**Funder**: {grant.funder}")
                if grant.pi_name:
                    st.markdown(f"**PI**: {grant.pi_name}")
                if grant.abstract_text:
                    st.markdown("**Abstract**")
                    st.markdown(f"> {grant.abstract_text[:500]}..." if len(grant.abstract_text) > 500 else f"> {grant.abstract_text}")
    else:
        st.info("No grant information available.")

def initialize_session_state():
    """Initialize all session state variables if they don't exist"""
    if 'researcher' not in st.session_state:
        st.session_state.researcher = None
    if 'processing_state' not in st.session_state:
        st.session_state.processing_state = "idle"
    if 'current_paper_index' not in st.session_state:
        st.session_state.current_paper_index = 0
    if 'publications_loaded' not in st.session_state:
        st.session_state.publications_loaded = False
    if 'grants_loaded' not in st.session_state:
        st.session_state.grants_loaded = False

def reset_session_state():
    """Reset session state for a new search"""
    st.session_state.researcher = None
    st.session_state.processing_state = "idle"
    st.session_state.current_paper_index = 0
    st.session_state.publications_loaded = False
    st.session_state.grants_loaded = False
    # Clear paper cache when starting a new search
    global _paper_cache
    _paper_cache = {}

def handle_search():
    """Handle the search button click"""
    reset_session_state()
    st.session_state.processing_state = "fetch_researcher"

async def process_papers_async():
    """Process papers asynchronously and update the session state"""
    researcher = await process_papers_in_batch(st.session_state.researcher)
    st.session_state.researcher = researcher
    st.session_state.publications_loaded = True
    st.session_state.processing_state = "fetch_grants"
    # No rerun needed as this will be called in a loop from main

def main():
    # Initialize components
    taxid_client = TaxIDLookup()

    # Set up page config
    st.set_page_config(
        page_title="ORCID to TAXID",
        page_icon="🧬",
        layout="wide"
    )
    st.title("🧬 ORCID to TAXID")
    st.markdown("Paste an ORCID ID to discover which pathogens "
                "a researcher has worked with before.")

    # Initialize session state
    initialize_session_state()

    # Move description and input to sidebar
    with st.sidebar:
        st.title("🧬 BioSec ProfileScout")
        # Input for ORCID ID
        orcid = st.text_input(
            "Enter ORCID ID",
            placeholder="e.g. 0000-0002-1825-0097",
            help="Enter the ORCID ID of the researcher you want to analyze"
        )
        # Add search button
        search_clicked = st.button("Search", type="primary", on_click=handle_search)

    # Create tabs for the main sections
    tab1, tab2, tab3 = st.tabs(["Researcher", "Publications", "Grants"])

    # Main application UI rendering logic
    with tab1:
        researcher_container = st.container()
        with researcher_container:
            if st.session_state.researcher:
                display_researcher_info(st.session_state.researcher)
            else:
                st.info("Enter an ORCID ID and click 'Search' to see researcher information.")

    with tab2:
        # Always create all containers unconditionally to avoid errors
        publications_container = st.container(height=200)
        organisms_container = st.container(height=200)
        highlights_container = st.container(height=200)
        
        with publications_container:
            st.subheader("📚 Publications")
        with organisms_container:
            st.subheader("🦠 Pathogens")
        with highlights_container:
            st.subheader("📌 Highlights")
    
        
        # Display the current progress if we're processing papers
        if st.session_state.processing_state in ["process_papers", "process_grants"]:
            if st.session_state.researcher and st.session_state.researcher.publications:
                num_papers = len(st.session_state.researcher.publications)
                if num_papers == 50:
                    st.success(f"Found more than {num_papers} publications, only 50 of them will be processed.")
                else:
                    st.success(f"Found {num_papers} publications")
        
        # Show results in the analysis tab
        if st.session_state.researcher:
            # Show publications as soon as they're fetched
            if st.session_state.researcher.publications:
                with publications_container:
                    # Display publications without waiting for processing
                    for paper in st.session_state.researcher.publications:
                        if paper.doi:
                            st.markdown(f"- [{paper.title}](https://doi.org/{paper.doi})")
                        else:
                            st.markdown(f"- {paper.title}")
            
            # Show processed results only after publications are processed
            if st.session_state.publications_loaded:
                with organisms_container:
                    display_organisms(st.session_state.researcher)
                
                with highlights_container:
                    display_highlights(st.session_state.researcher)

    with tab3:
        grants_container = st.container()
        with grants_container:
            st.subheader("Grants")
            if st.session_state.researcher and st.session_state.grants_loaded:
                display_grants(st.session_state.researcher)
            else:
                st.info("Grant information will appear here after searching.")

    # Processing state machine
    if st.session_state.processing_state == "fetch_researcher":
        with researcher_container:
            with st.spinner("Fetching researcher information..."):
                researcher = fetch_researcher_by_orcid(orcid)
                st.session_state.researcher = researcher
                st.session_state.processing_state = "fetch_publications"
                st.rerun()
    
    elif st.session_state.processing_state == "fetch_publications":
        with publications_container:
            with st.spinner("Fetching publications..."):
                researcher = fetch_publications(st.session_state.researcher)
                st.session_state.researcher = researcher
                
                if not researcher.publications:
                    st.session_state.publications_loaded = True
                    st.session_state.processing_state = "fetch_grants"
                else:
                    st.session_state.processing_state = "process_papers"
                st.rerun()
    
    elif st.session_state.processing_state == "process_papers":
        with organisms_container:
            with st.spinner("Processing publications to extract organisms..."):
                # Create a new async task to process papers
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(process_papers_async())
                    st.rerun()
                finally:
                    loop.close()
    
    elif st.session_state.processing_state == "fetch_grants":
        with grants_container:
            with st.spinner("Fetching grants information..."):
                researcher = fetch_grants(st.session_state.researcher)
                st.session_state.researcher = researcher
                st.session_state.grants_loaded = True
                st.session_state.processing_state = "complete"
                st.rerun()

if __name__ == "__main__":
    main()