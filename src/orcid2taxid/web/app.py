import streamlit as st
from orcid2taxid.integrations.europe_pmc import EuropePMCRepository
from orcid2taxid.analysis.extraction.papers import PaperExtractor
from orcid2taxid.integrations.ncbi import TaxIDLookup
from collections import defaultdict
from typing import List
from orcid2taxid.core.models.schemas import PaperMetadata, OrganismMention

# Custom hash functions for Pydantic models
def hash_paper_metadata(paper: PaperMetadata) -> tuple:
    """Create a hashable tuple from essential paper fields"""
    return (
        paper.title,
        paper.abstract,
        paper.doi,
        paper.publication_date
    )

@st.cache_data(hash_funcs={PaperMetadata: hash_paper_metadata})
def fetch_publications(orcid: str, max_results: int = 20) -> List[PaperMetadata]:
    """Cached function to fetch publications from Europe PMC"""
    return europe_pmc.get_publications_by_orcid(orcid, max_results=max_results)

@st.cache_data(hash_funcs={PaperMetadata: hash_paper_metadata})
def extract_organisms_from_paper(paper: PaperMetadata) -> List[OrganismMention]:
    """Cached function to extract organisms from a paper"""
    return organism_extractor.extract_organisms_from_abstract(paper)

def display_results():
    """Display both organisms and papers in a single update"""
    # Display organisms
    if st.session_state.organism_to_papers:
        st.subheader("🦠 Organisms Identified")
        for (scientific_name, taxid), papers in st.session_state.organism_to_papers.items():
            with st.expander(f"{scientific_name} (TAXID: {taxid})"):
                for paper in papers:
                    st.markdown(f"**{paper['title']}** ({paper['year']})")
                    if paper['doi']:
                        st.markdown(f"DOI: [{paper['doi']}](https://doi.org/{paper['doi']})")
                    st.markdown("---")
    
    # Display papers
    if st.session_state.analyzed_papers:
        st.subheader("📚 Analyzed Papers")
        for paper in st.session_state.analyzed_papers:
            with st.expander(f"{paper.title} ({paper.publication_date[:4] if paper.publication_date else 'Unknown'})"):
                if paper.doi:
                    st.markdown(f"**DOI**: [{paper.doi}](https://doi.org/{paper.doi})")
                if paper.abstract:
                    st.markdown("**Abstract**")
                    st.markdown(f"> {paper.abstract}")
                else:
                    st.markdown("*No abstract available*")

def handle_search():
    """Handle the search button click"""
    # Reset the data
    st.session_state.organism_to_papers = defaultdict(list)
    st.session_state.analyzed_papers = []

# Initialize components
europe_pmc = EuropePMCRepository()
organism_extractor = PaperExtractor()
taxid_client = TaxIDLookup()

# Set up page config
st.set_page_config(
    page_title="ORCID to TAXID",
    page_icon="🧬",
    layout="wide"
)
st.title("🧬 ORCID to TAXID")
st.markdown("Paste an ORCID ID to discover which dangerous organisms "
            "a researcher has worked with before.")

# Initialize session state
if 'organism_to_papers' not in st.session_state:
    st.session_state.organism_to_papers = defaultdict(list)
if 'analyzed_papers' not in st.session_state:
    st.session_state.analyzed_papers = []

# Move description and input to sidebar
with st.sidebar:
    st.title("🧬 ORCID to TAXID")
    st.markdown("""
    This app helps you discover which organisms a researcher has worked with based on their publications.
    Just enter an ORCID ID and we'll:
    1. Fetch their publications
    2. Analyze them for organism mentions
    3. Map those organisms to their NCBI Taxonomy IDs
    """)

    # Input for ORCID ID
    orcid = st.text_input(
        "Enter ORCID ID",
        placeholder="e.g. 0000-0002-1825-0097",
        help="Enter the ORCID ID of the researcher you want to analyze"
    )

    # Add number input for max papers
    max_papers = st.number_input(
        "Maximum number of papers",
        min_value=1,
        max_value=100,
        value=20,
        help="Maximum number of papers to analyze"
    )

    # Add search button
    search_clicked = st.button("Search", type="primary", on_click=handle_search)

# Main content area
if orcid and search_clicked:
    with st.spinner("Fetching publications..."):
        # Get publications using cached function
        publications = fetch_publications(orcid, max_results=max_papers)
        if not publications:
            st.warning("No publications found for this ORCID ID")
        else:
            st.success(f"Found {len(publications)} publications")
            
            # Create a status container for current paper
            status_container = st.empty()
            progress_bar = st.progress(0)
            results_placeholder = st.empty()
            
            for i, paper in enumerate(publications):
                # Update status
                status_container.text(f"Processing: {paper.title[:180]}...")
                
                # Store paper for display
                st.session_state.analyzed_papers.append(paper)
                
                # Extract organisms using cached function
                organisms = extract_organisms_from_paper(paper)
                
                # For each organism, look up its taxonomy info and store paper reference
                for organism in organisms:
                    # Get taxonomy info
                    tax_info = taxid_client.get_taxid(organism.searchable_name)
                    if tax_info:
                        # Create a key that includes scientific name and taxid
                        key = (tax_info.scientific_name, tax_info.taxid)
                        # Store paper reference if not already present
                        paper_info = {
                            'title': paper.title,
                            'doi': paper.doi,
                            'year': paper.publication_date[:4] if paper.publication_date else 'Unknown'
                        }
                        if paper_info not in st.session_state.organism_to_papers[key]:
                            st.session_state.organism_to_papers[key].append(paper_info)
                
                with results_placeholder:
                    with st.container():
                        display_results()
                # Update progress
                progress_bar.progress((i + 1) / len(publications))