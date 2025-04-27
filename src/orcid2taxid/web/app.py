import streamlit as st
import asyncio
import base64
from pathlib import Path
from orcid2taxid.organisms.integrations.ncbi import TaxIDLookup
from orcid2taxid.researchers.services import get_researcher_by_orcid, find_publications
from orcid2taxid.publications.services import get_classification, get_organisms, get_taxonomy_info, process_paper_async
from orcid2taxid.grants.services import find_grants
from orcid2taxid.core.models.customer import PublicationRecord, ResearcherProfile, GrantMetadata, PaperClassificationMetadata

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

def hash_researcher_metadata(researcher: ResearcherProfile) -> tuple:
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
def fetch_researcher_by_orcid(orcid: str) -> ResearcherProfile:
    """Cached function to fetch basic researcher metadata"""
    return get_researcher_by_orcid(orcid)

@st.cache_data(hash_funcs={ResearcherProfile: hash_researcher_metadata})
def fetch_publications(researcher: ResearcherProfile) -> ResearcherProfile:
    """Cached function to fetch publications for a researcher
    
    Uses underscore prefix to prevent Streamlit from hashing the researcher object"""
    return find_publications(researcher, max_results=50)

@st.cache_data(hash_funcs={ResearcherProfile: hash_researcher_metadata})
def fetch_grants(researcher: ResearcherProfile) -> ResearcherProfile:
    """Cached function to fetch grants for a researcher
    
    Uses underscore prefix to prevent Streamlit from hashing the researcher object"""
    return find_grants(researcher)

@st.cache_data(hash_funcs={PublicationRecord: hash_paper_metadata})
def extract_organisms_from_paper(paper: PublicationRecord) -> PublicationRecord:
    """Cached function to extract organisms from a paper
    
    Uses underscore prefix to prevent Streamlit from hashing the paper object"""
    return get_organisms(paper)

@st.cache_data(hash_funcs={PublicationRecord: hash_paper_metadata})
def classify_paper(paper: PublicationRecord) -> PublicationRecord:
    """Cached function to classify a paper
    
    Uses underscore prefix to prevent Streamlit from hashing the paper object"""
    return get_classification(paper)

@st.cache_data(hash_funcs={PublicationRecord: hash_paper_metadata})
def get_taxonomy(paper: PublicationRecord) -> PublicationRecord:
    """Cached function to get taxonomy info for a paper
    
    Uses underscore prefix to prevent Streamlit from hashing the paper object"""
    return get_taxonomy_info(paper)


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
    processed_paper = await process_paper_async(paper)
    
    # Cache the result
    _paper_cache[cache_key] = processed_paper
    
    return processed_paper

def process_single_paper(researcher: ResearcherProfile, paper_index: int, taxid_client: TaxIDLookup) -> ResearcherProfile:
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

async def process_papers_in_batch(researcher: ResearcherProfile, batch_size: int = 10) -> ResearcherProfile:
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
        processed_papers = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update papers in researcher object
        for j, processed_paper in enumerate(processed_papers):
            if not isinstance(processed_paper, Exception):
                researcher.publications[i+j] = processed_paper
            
    return researcher

def display_researcher_info(researcher: ResearcherProfile):
    """Display researcher information"""
    if st.session_state.researcher:
        st.subheader("Researcher Profile")
        full_name = f"{researcher.given_name} {researcher.family_name}"
        st.markdown(f"**Name:** {full_name}")
        
        # Display affiliations
        st.markdown("#### Employment History")
        if researcher.affiliations:
            # Get affiliations grouped by institution
            by_institution = researcher.get_affiliations_by_institution()
            
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
        if researcher.education:
            # Sort education by start date in descending order (most recent first)
            sorted_education = sorted(
                [e for e in researcher.education if e.start_date],
                key=lambda x: x.start_date,
                reverse=True
            )
            
            for education in sorted_education:
                # Format the education line
                education_line = f"- {education.institution_name}"
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

def display_highlights(researcher: ResearcherProfile):
    """Display paper highlights from the researcher's publications"""
    processed_papers = [p for p in researcher.publications if p.classification and isinstance(p.classification, PaperClassificationMetadata)]
    
    # Group papers by highlight type
    highlight_groups = {
        "wet_lab": [],
        "bsl_2": [],
        "bsl_3": [],
        "bsl_4": [],
        "vaccine": [],
        "synthetic_genome": []
    }
    
    # Group papers by highlight type
    for paper in processed_papers:
        if paper.classification.wet_lab_work == "yes":
            highlight_groups["wet_lab"].append(paper)
        
        # if paper.classification.bsl_level == "bsl_2":
        #     highlight_groups["bsl_2"].append(paper)
        # elif paper.classification.bsl_level == "bsl_3":
        #     highlight_groups["bsl_3"].append(paper)
        # elif paper.classification.bsl_level == "bsl_4":
        #     highlight_groups["bsl_4"].append(paper)
        
        if "vaccine_development" in paper.classification.dna_use:
            highlight_groups["vaccine"].append(paper)
        
        if "synthetic_genome" in paper.classification.dna_type:
            highlight_groups["synthetic_genome"].append(paper)
    
    def get_paper_list(papers: list[PublicationRecord]) -> str:
        markdown_list = []
        for paper in papers:
            paper_link = f"[{paper.title}](https://doi.org/{paper.doi})" if paper.doi else paper.title
            markdown_list.append(f"* {paper_link}")
        return "\n\n".join(markdown_list)
    
    # Display highlights in checklist format
    if any(highlight_groups.values()):
        if papers := highlight_groups["wet_lab"]:
            st.markdown("- [x] Has done wet lab work", help=get_paper_list(papers))
        
        # if papers := highlight_groups["bsl_2"]:
        #     st.markdown("- [x] Has done work requiring a BSL-2 lab", help=get_paper_list(papers))
        
        # if papers := highlight_groups["bsl_3"]:
        #     st.markdown("- [x] Has done work requiring a BSL-3 lab", help=get_paper_list(papers))
        
        # if papers := highlight_groups["bsl_4"]:
        #     st.markdown("- [x] Has done work requiring a BSL-4 lab", help=get_paper_list(papers))
        
        if papers := highlight_groups["vaccine"]:
            st.markdown("- [x] Has done vaccine development work", help=get_paper_list(papers))
        
        if papers := highlight_groups["synthetic_genome"]:
            st.markdown("- [x] Has done synthetic genome work", help=get_paper_list(papers))
    else:
        st.info("No highlights detected in the analyzed papers.")

def display_organisms(researcher: ResearcherProfile):
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
        st.info("No organisms were identified in the researcher's publications.")

def display_papers(researcher: ResearcherProfile):
    """Display paper list from the researcher's publications"""
    for paper in researcher.publications:
        if paper.doi:
            st.markdown(f"- [{paper.title}](https://doi.org/{paper.doi})")
        else:
            st.markdown(f"- {paper.title}")

def display_grants(researcher: ResearcherProfile):
    """Display grant information from the researcher's grants"""
    if researcher.grants:
        # Get grants grouped by funder
        grants_by_funder = researcher.get_grants_by_funder()
        
        # Display grants for each funder group
        for funder, grants in grants_by_funder.items():
            st.subheader(funder)
            for grant in grants:
                # Create expander title using project title or number
                title_part = grant.project_title if grant.project_title else f"Project {grant.project_num}"
                expander_title = f"{title_part[:100]}{'...' if len(title_part) > 100 else ''}"
                
                with st.expander(expander_title):
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
    highlights_container = st.container(height=300)
    
    with publications_container:
        st.subheader("📖 Publications")
    with organisms_container:
        st.subheader("🦠 Pathogens")
    with highlights_container:
        st.subheader("📌 Highlights")
        
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
        with highlights_container:
            display_highlights(st.session_state.researcher)
    
    return publications_container, organisms_container, highlights_container

def render_grants_tab():
    """Render the grants tab content"""
    grants_container = st.container()
    with grants_container:
        st.subheader("Grants")
        if st.session_state.researcher and st.session_state.grants_loaded:
            display_grants(st.session_state.researcher)
        else:
            st.info("Grant information will appear here after searching.")
    return grants_container
    
def handle_processing_state(
    researcher_container,
    publications_container,
    organisms_container,
    highlights_container,
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
            for container in [publications_container, organisms_container, highlights_container]:
                with container:
                    st.info(no_publications_message)
            st.session_state.publications_loaded = True
            st.session_state.processing_state = "fetch_grants"
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
        publications_container, organisms_container, highlights_container = render_publications_tab()

    with tab3:
        grants_container = render_grants_tab()
        
    # Handle processing state
    handle_processing_state(
        researcher_container,
        publications_container,
        organisms_container,
        highlights_container,
        grants_container
    )

if __name__ == "__main__":
    main()