import asyncio
import base64
from datetime import datetime
from pathlib import Path

import streamlit as st

from orcid2taxid.publication.schemas import PublicationRecord
from orcid2taxid.researcher.schemas import CustomerProfile
from orcid2taxid.grant.schemas.base import GrantRecord

from orcid2taxid.researcher.services import get_customer_profile, collect_customer_publications
from orcid2taxid.publication.services import collect_publication_organisms
from orcid2taxid.grant.services import find_grants
from orcid2taxid.shared.schemas import ResearcherID

# Custom hash functions for Pydantic models
def hash_paper_metadata(paper: PublicationRecord) -> tuple:
    """Create a hashable tuple from essential paper fields"""
    return (
        paper.title,
        paper.abstract,
        paper.doi,
        paper.publication_date,
        paper.journal_name,  # Added to improve uniqueness
        # Include a hash of authors' names if available
        tuple(getattr(author.researcher_id, "full_name", None) or f"{author.researcher_id.given_name} {author.researcher_id.family_name}" 
              for author in paper.authors) if paper.authors else None
    )

def hash_grant_metadata(grant: GrantRecord) -> tuple:
    """Create a hashable tuple from essential grant fields"""
    return (
        grant.title,
        grant.id,
        grant.funder,
        # Get PI name from principal_investigators if available
        getattr(grant.principal_investigators[0], 'credit_name', None) if grant.principal_investigators else None,
        grant.start_date  # Added to distinguish between versions of the same grant
    )

def hash_researcher_metadata(researcher: CustomerProfile) -> tuple:
    """Create a hashable tuple from essential researcher fields"""
    return (
        researcher.researcher_id.orcid,
        researcher.researcher_id.full_name if hasattr(researcher.researcher_id, 'full_name') else None,
        researcher.researcher_id.given_name,
        researcher.researcher_id.family_name,
        # Use researcher_id's last_modified if available, otherwise None
        getattr(researcher.researcher_id, 'last_modified', None),
        len(researcher.publications)  # Added to detect when publications have been added
    )

@st.cache_data()
def fetch_researcher_by_orcid(orcid: str) -> CustomerProfile:
    """Cached function to fetch basic researcher metadata"""
    customer_id = ResearcherID(
        orcid=orcid,
        given_name="",
        family_name="",
    )
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(get_customer_profile(customer_id))
    finally:
        loop.close()

@st.cache_data(hash_funcs={CustomerProfile: hash_researcher_metadata})
def fetch_publications(researcher: CustomerProfile) -> CustomerProfile:
    """Cached function to fetch publications for a researcher
    
    Uses underscore prefix to prevent Streamlit from hashing the researcher object"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(collect_customer_publications(researcher, max_results=50))
    finally:
        loop.close()

@st.cache_data(hash_funcs={CustomerProfile: hash_researcher_metadata})
def fetch_grants(researcher: CustomerProfile) -> CustomerProfile:
    """Cached function to fetch grants for a researcher
    
    Uses hash_researcher_metadata to prevent Streamlit from hashing the researcher object"""
    loop = asyncio.new_event_loop()
    try:
        # Pass the researcher and max_results to find_grants
        return loop.run_until_complete(find_grants(researcher, max_results=50))
    finally:
        loop.close()

@st.cache_data(hash_funcs={PublicationRecord: hash_paper_metadata})
def extract_organisms_from_paper(paper: PublicationRecord) -> PublicationRecord:
    """Cached function to extract organisms from a paper
    
    Uses underscore prefix to prevent Streamlit from hashing the paper object"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(collect_publication_organisms(paper))
    finally:
        loop.close()

# @st.cache_data(hash_funcs={PublicationRecord: hash_paper_metadata})
# def classify_paper(paper: PublicationRecord) -> PublicationRecord:
#     """Cached function to classify a paper
    
#     Uses underscore prefix to prevent Streamlit from hashing the paper object"""
#     return get_classification(paper)

# @st.cache_data(hash_funcs={PublicationRecord: hash_paper_metadata})
# def get_taxonomy(paper: PublicationRecord) -> PublicationRecord:
#     """Cached function to get taxonomy info for a paper
    
#     Uses underscore prefix to prevent Streamlit from hashing the paper object"""
#     return get_taxonomy_info(paper)


# We'll maintain a simple in-memory cache for processed papers
_paper_cache = {}

async def process_paper_async_wrapper(paper: PublicationRecord) -> PublicationRecord:
    """Async wrapper for processing a paper that checks an in-memory cache first"""
    # Create a cache key using the hash_paper_metadata function
    cache_key = hash_paper_metadata(paper)
    
    # Check if we already processed this paper
    if cache_key in _paper_cache:
        return _paper_cache[cache_key]
    
    # Process the paper
    try:
        processed_paper = await collect_publication_organisms(paper)
        
        # Cache the result
        _paper_cache[cache_key] = processed_paper
        
        return processed_paper
    except Exception as e:
        print(f"Error processing paper {paper.title[:50]}: {str(e)}")
        # Return the original paper if there's an error
        return paper

def process_single_paper(researcher: CustomerProfile, paper_index: int) -> CustomerProfile:
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
    
    # Update the paper in the researcher object
    researcher.publications[paper_index] = updated_paper
    return researcher

async def process_papers_in_batch(researcher: CustomerProfile) -> CustomerProfile:
    """Process all papers asynchronously
    
    This function processes all papers in parallel at once.
    Rate limits are handled within the extraction functions.
    
    Returns the updated researcher object
    """
    if not researcher.publications:
        return researcher
        
    # Check if publications have abstracts
    have_abstract = 0
    missing_abstract = 0
    for i, paper in enumerate(researcher.publications):
        if paper.abstract:
            have_abstract += 1
        else:
            missing_abstract += 1
    
    # Process all papers at once asynchronously
    tasks = [process_paper_async_wrapper(paper) for paper in researcher.publications]
    try:
        processed_papers = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update papers in researcher object
        successful_updates = 0
        for i, processed_paper in enumerate(processed_papers):
            if not isinstance(processed_paper, Exception):
                researcher.publications[i] = processed_paper
                successful_updates += 1
            else:
                pass
        
    except Exception as e:
        pass
    return researcher

def display_researcher_info(researcher: CustomerProfile):
    """Display researcher information"""
    if st.session_state.researcher:
        st.subheader("Researcher Profile")
        st.markdown(f"**Name:** {researcher.researcher_id.full_name}")
        
        # Display affiliations
        st.markdown("#### Employment History")
        if researcher.employments:
            # Group employments by institution
            by_institution = {}
            for employment in researcher.employments:
                if employment.institution not in by_institution:
                    by_institution[employment.institution] = []
                by_institution[employment.institution].append(employment)
            
            # Display each institution and its roles
            for institution, affiliations in by_institution.items():
                st.markdown(f"**{institution}**")
                for affiliation in affiliations:
                    # Format time range and role
                    time_range = researcher.format_affiliation_time_range(affiliation)
                    role_info = researcher.format_affiliation_role(affiliation)
                    
                    # Create the role line
                    role_line = " - "
                    if role_info:
                        role_line += role_info
                    else:
                        role_line += "Unknown role"
                    if time_range:
                        role_line += f" {time_range}"
                    st.markdown(role_line)
        else:
            st.info("No employment history found on their ORCID profile.")
        
        # Display education
        st.markdown("#### Education")
        if researcher.educations:
            # Sort education by start date in descending order (most recent first)
            sorted_education = sorted(
                [e for e in researcher.educations if e.start_date],
                key=lambda x: x.start_date,
                reverse=True
            )
            
            for education in sorted_education:
                # Format the education line
                education_line = f"- {education.institution}"
                if education.department:
                    education_line += f", {education.department}"
                if education.role:  # Add degree/field if available
                    education_line += f" ({education.role})"
                
                # Add time range if available
                time_range = researcher.format_education_time_range(education)
                if time_range:
                    education_line += f" {time_range}"
                    
                st.markdown(education_line)
        else:
            st.info("No education history found on their ORCID profile.")
    else:
        st.info("Enter an ORCID ID and click 'Search' to see researcher information.")


def display_organisms(researcher: CustomerProfile):
    """Display organisms from the researcher's publications"""
    organism_to_papers = researcher.get_publications_by_organism()
    
    if organism_to_papers:
        for scientific_name, papers_list in organism_to_papers.items():
            # Get the first paper's organism to access taxonomy info
            first_paper = papers_list[0]
            organism = next((o for o in first_paper.organisms if o.taxonomy and o.taxonomy.scientific_name == scientific_name), None)
            
            if not organism:
                continue
                
            taxid = organism.taxonomy.taxid
            
            # Create help text with context and paper links
            help_text = []
            for paper in papers_list:
                # Find the organism mention in this paper
                paper_organism = next((o for o in paper.organisms if o.taxonomy and o.taxonomy.scientific_name == scientific_name), None)
                if not paper_organism:
                    continue
                    
                context = f'"{paper_organism.quote}"' if paper_organism.quote else "No context available"
                
                # Create paper link if DOI is available
                paper_link = f"[(link)](https://doi.org/{paper.doi})" if paper.doi else paper.title
                help_text.append(f"* {context} {paper_link}")
            
            taxid_link = f"[TaxID {taxid}](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={taxid})"
            st.markdown(f"- **{scientific_name.capitalize()}** ({taxid_link})", help="\n\n".join(help_text))
    else:
        st.info("No organisms were identified in the researcher's publications.")

def display_papers(researcher: CustomerProfile):
    """Display paper list from the researcher's publications"""
    for paper in researcher.publications:
        if paper.doi:
            st.markdown(f"- [{paper.title}](https://doi.org/{paper.doi})")
        else:
            st.markdown(f"- {paper.title}")

def display_grants(researcher: CustomerProfile):
    """Display grant information from the researcher's grants"""
    if researcher.grants:
        # Get grants grouped by funder
        grants_by_funder = researcher.get_grants_by_funder()
        
        # Display grants by funder
        st.markdown(f"Found {len(researcher.grants)} grants associated with the researcher")
        
        # Create expanders for each funder
        for funder, grants in grants_by_funder.items():
            with st.expander(f"{funder} ({len(grants)} grants)"):
                _display_grants_list(grants)
    else:
        st.info("No grants found for this researcher.")
        
def _display_grants_list(grants):
    """Helper function to display a list of grants"""
    # Grants are already sorted by date in get_grants_by_funder
    for i, grant in enumerate(grants):
        # Use title or grant ID as header
        header = grant.title if grant.title else f"Grant {grant.id}" if grant.id else f"Untitled Grant {i+1}"
        st.markdown(f"### {header}")
        
        if grant.id:
            st.markdown(f"**Project Number:** {grant.id}")
        
        # Display PI information
        if grant.principal_investigators:
            pi_names = [f"{pi.given_name} {pi.family_name}" for pi in grant.principal_investigators]
            st.markdown(f"**Principal Investigators:** {', '.join(pi_names)}")
        
        # Display dates if available
        date_info = []
        if grant.start_date:
            date_info.append(f"{grant.start_date.strftime('%Y-%m-%d')}")
        if grant.end_date:
            date_info.append(f"{grant.end_date.strftime('%Y-%m-%d')}")
        if date_info:
            st.markdown(f"**Project Period:** {' to '.join(date_info)}")
        
        # Display status
        if grant.is_active is not None:
            status = "Active" if grant.is_active else "Inactive"
            st.markdown(f"**Status:** {status}")
            
        # Display financial information if available
        if grant.amount is not None:
            currency = grant.currency or 'USD'
            st.markdown(f"**Amount:** {currency} {grant.amount:,.2f}")
        if grant.year:
            st.markdown(f"**Fiscal Year:** {grant.year}")
        
        # Display source DOI if available
        if grant.source_doi:
            st.markdown(f"**Source Publication DOI:** [doi:{grant.source_doi}](https://doi.org/{grant.source_doi})")
        
        # Add a divider between grants
        # Display abstract if available
        if grant.abstract:
            st.markdown("**Abstract:**")
            st.markdown(grant.abstract)
        
        # Display keywords if available (limited to 20, comma-separated)
        if grant.keywords:
            keywords_to_show = grant.keywords[:20]
            extra_keyword_message = (f"*...and {len(grant.keywords) - 20} more keywords*" 
                                     if len(grant.keywords) > 20 else "")
            st.markdown(f"**Keywords:** {', '.join(keywords_to_show)} {extra_keyword_message}")
        
        if i < len(grants) - 1:
            st.markdown("---")

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
    try:
        researcher = await process_papers_in_batch(st.session_state.researcher)
        st.session_state.researcher = researcher
        st.session_state.publications_loaded = True
        st.session_state.processing_state = "fetch_grants"
        # No rerun needed as this will be called in a loop from main
    except Exception as e:
        # Still mark as loaded to prevent endless error loops
        st.session_state.publications_loaded = True
        st.session_state.processing_state = "fetch_grants"

def get_base64_encoded_image(filename: str) -> tuple[str, str]:
    """Get base64 encoded image from file path"""
    image_path = Path(__file__).parent / "assets" / filename
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return (
        f'<img src="data:image/png;base64,{encoded_string}" style="height: 64px; margin-right: 10px; vertical-align: middle;">',
        encoded_string
    )

def setup_page_style():
    """Setup page style with custom fonts and CSS"""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        
        .title-text {
            font-family: 'Roboto', sans-serif;
            font-size: 48px;
            vertical-align: middle;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_header():
    """Render the page header with logo and title"""
    logo_html, _ = get_base64_encoded_image("rose-scout-logo.png")
    st.markdown(f'{logo_html}<span class="title-text">ROSE Scout</span>', unsafe_allow_html=True)
    st.markdown("Rapid researcher profiling to simplify DNA synthesis screening.")
    # st.markdown("Discover which pathogens a researcher has worked with before.")

def render_sidebar():
    """Render the sidebar content"""
    with st.sidebar:
        st.title("ROSE Scout")
        
        # Input for ORCID ID
        orcid = st.text_input(
            "Enter ORCID ID",
            placeholder="e.g. 0000-0002-1825-0097",
            help="Enter the ORCID ID of the researcher you want to analyze"
        )
        search_clicked = st.button("Search", type="primary", on_click=handle_search)
        
        st.markdown("""
            ROSE Scout fetches information from:
            - [ORCID](https://orcid.org/)
            - [PubMed](https://pubmed.ncbi.nlm.nih.gov/) 
            - [NIH RePORTER](https://reporter.nih.gov/)
            - [NSF Grant Data](https://www.nsf.gov/awardsearch/)
        """)
        
        # Add feature request message at the bottom
        st.markdown("---")  # Add a horizontal line for separation
        st.markdown("""
                    Don't see what you're looking for?  
                    [Request a feature here!](https://docs.google.com/forms/d/e/1FAIpQLSd4vxRtwB_f7cUo_hfeTLHUAqH9qZOZ4fvAKBBQa-NuIMC8SA/viewform)
        """)
        
        return orcid, search_clicked

def render_publications_tab():
    """Render the publications tab content"""
    publications_container = st.container(height=300)
    organisms_container = st.container(height=300)
    
    with publications_container:
        st.subheader("📖 Publications")
    with organisms_container:
        st.subheader("🦠 Pathogens")
        
    # Show publications as soon as they're available
    if st.session_state.researcher:
        num_papers = len(st.session_state.researcher.publications)
        if num_papers > 0:
            if num_papers == 50:
                publications_container.markdown("Found more than 50 publications, only 50 of them will be processed:")
            else:
                publications_container.markdown(f"Found {num_papers} publications:")
            
            with publications_container:
                display_papers(st.session_state.researcher)
        
        if num_papers == 0 and st.session_state.publications_loaded:
            publications_container.info("No publications found associated with the researcher's ORCID.")
        
    else:
        with publications_container:
            st.info("No publications found yet.")
    
    # Show organisms and highlights only after processing is complete
    if st.session_state.researcher and st.session_state.publications_loaded:
        with organisms_container:
            display_organisms(st.session_state.researcher)
    
    return publications_container, organisms_container

def render_grants_tab():
    """Render the grants tab content"""
    grants_container = st.container()
    with grants_container:
        st.subheader("🏦 Research Grants")
        
        if st.session_state.researcher and st.session_state.grants_loaded:
            display_grants(st.session_state.researcher)
        else:
            st.info("Grant information will appear here after searching.")
            
    return grants_container
    
def handle_processing_state(
    researcher_container,
    publications_container,
    organisms_container,
    grants_container
):
    """Handle the processing state machine"""    
    # State machine for processing
    
    if st.session_state.processing_state == "fetch_researcher":
        with researcher_container:
            with st.spinner("Fetching researcher information..."):
                researcher = fetch_researcher_by_orcid(st.session_state.orcid)
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
        if st.session_state.researcher.publications:
            with organisms_container:
                with st.spinner("Processing publications to extract organisms..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(process_papers_async())
                        st.session_state.publications_loaded = True
                        st.session_state.processing_state = "fetch_grants"
                        st.rerun()
                    finally:
                        loop.close()
        else:
            no_publications_message = "We didn't find any publications associated with the researcher's ORCID"
            for container in [publications_container, organisms_container]:
                with container:
                    st.info(no_publications_message)
            st.session_state.publications_loaded = True
            # st.session_state.processing_state = "fetch_grants"
            st.session_state.processing_state = "complete"
            st.rerun()
    
    elif st.session_state.processing_state == "fetch_grants":
        with grants_container:
            with st.spinner("Fetching grants information..."):
                researcher = fetch_grants(st.session_state.researcher)
                st.session_state.researcher = researcher
                st.session_state.grants_loaded = True
                st.session_state.processing_state = "complete"
                st.rerun()

def setup_page_config():
    """Configure the Streamlit page settings"""
    # Get raw base64 for page icon
    _, icon_base64 = get_base64_encoded_image("rose-scout-logo-strong-edge.png")
    
    # Configure the page
    st.set_page_config(
        page_title="ROSE Scout",
        page_icon=f"data:image/png;base64,{icon_base64}",
        layout="wide"
    )

def main():
    # Configure the page
    setup_page_config()
    initialize_session_state()
    setup_page_style()
    render_header()
    
    # Render sidebar and get user input
    orcid, _ = render_sidebar()
    if orcid:
        st.session_state.orcid = orcid
    
    # Render main content tabs
    tab1, tab2, tab3 = st.tabs(["Researcher", "Publications", "Grants"])

    with tab1:
        researcher_container = st.container()
        with researcher_container:
            display_researcher_info(st.session_state.researcher)

    with tab2:
        publications_container, organisms_container = render_publications_tab()

    with tab3:
        grants_container = render_grants_tab()
        
    # Handle processing state
    handle_processing_state(
        researcher_container,
        publications_container,
        organisms_container,
        grants_container
    )

if __name__ == "__main__":
    main()