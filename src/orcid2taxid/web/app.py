import asyncio
import base64
from pathlib import Path

import streamlit as st

from orcid2taxid.publication.schemas import PublicationRecord
from orcid2taxid.researcher.schemas import CustomerProfile
from orcid2taxid.grant.schemas.base import GrantRecord

from orcid2taxid.researcher.services import get_customer_profile, collect_customer_publications
from orcid2taxid.publication.services import collect_publication_organisms
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
        grant.project_title,
        grant.project_num,
        grant.funder,
        grant.pi_name,  # Added to improve uniqueness
        grant.project_start_date  # Added to distinguish between versions of the same grant
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
        from orcid2taxid.grant.services import find_grants
        return loop.run_until_complete(find_grants(researcher))
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
    print(f"Processing paper: {paper.title[:50]}...")
    cache_key = hash_paper_metadata(paper)
    
    # Check if we already processed this paper
    if cache_key in _paper_cache:
        print(f"Using cached result for paper: {paper.title[:50]}...")
        return _paper_cache[cache_key]
    
    # Process the paper
    try:
        print(f"Calling collect_publication_organisms for paper: {paper.title[:50]}...")
        processed_paper = await collect_publication_organisms(paper)
        print(f"Successfully processed paper: {paper.title[:50]}")
        
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

async def process_papers_in_batch(researcher: CustomerProfile, batch_size: int = 10) -> CustomerProfile:
    """Process papers in batches asynchronously
    
    This function processes papers in batches to respect rate limits while
    maximizing concurrency. Each batch is processed in parallel.
    
    Returns the updated researcher object
    """
    print(f"Starting process_papers_in_batch with {len(researcher.publications)} publications")
    if not researcher.publications:
        print("No publications to process")
        return researcher
        
    # Check if publications have abstracts
    have_abstract = 0
    missing_abstract = 0
    for i, paper in enumerate(researcher.publications):
        if paper.abstract:
            have_abstract += 1
        else:
            missing_abstract += 1
            print(f"Publication {i} is missing an abstract: {paper.title[:50]}")
    
    print(f"Publications with abstracts: {have_abstract}, without abstracts: {missing_abstract}")
    
    # Process papers in batches
    for i in range(0, len(researcher.publications), batch_size):
        batch = researcher.publications[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1} with {len(batch)} papers")
        
        # Process batch asynchronously
        tasks = [process_paper_async_wrapper(paper) for paper in batch]
        try:
            processed_papers = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update papers in researcher object
            successful_updates = 0
            for j, processed_paper in enumerate(processed_papers):
                if not isinstance(processed_paper, Exception):
                    researcher.publications[i+j] = processed_paper
                    successful_updates += 1
                else:
                    print(f"Error in paper {i+j}: {str(processed_paper)}")
            
            print(f"Successfully processed {successful_updates}/{len(batch)} papers in batch {i//batch_size + 1}")
        except Exception as e:
            print(f"Error processing batch {i//batch_size + 1}: {str(e)}")
            
    print(f"Finished processing all {len(researcher.publications)} papers")
    return researcher

def display_researcher_info(researcher: CustomerProfile):
    """Display researcher information"""
    if st.session_state.researcher:
        st.subheader("Researcher Profile")
        full_name = f"{researcher.researcher_id.given_name} {researcher.researcher_id.family_name}"
        st.markdown(f"**Name:** {full_name}")
        
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
                print(f"Warning: Could not find organism with scientific_name={scientific_name} in paper")
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
        st.subheader(f"Grants ({len(researcher.grants)} total)")
        
        # Create tabs for each funder
        if len(grants_by_funder) > 1:
            funder_tabs = st.tabs(list(grants_by_funder.keys()))
            
            for i, (funder, grants) in enumerate(grants_by_funder.items()):
                with funder_tabs[i]:
                    st.write(f"**{len(grants)} grants from {funder}**")
                    _display_grants_list(grants)
        else:
            # If there's only one funder, don't use tabs
            for funder, grants in grants_by_funder.items():
                st.write(f"**{len(grants)} grants from {funder}**")
                _display_grants_list(grants)
    else:
        st.info("No grants found for this researcher.")
        
def _display_grants_list(grants):
    """Helper function to display a list of grants"""
    for i, grant in enumerate(grants):
        with st.expander(f"{grant.title or 'Untitled Grant'}"):
            cols = st.columns([3, 1])
            
            with cols[0]:
                if grant.title:
                    st.markdown(f"**Title:** {grant.title}")
                if grant.id:
                    st.markdown(f"**Project Number:** {grant.id}")
                if grant.funder:
                    st.markdown(f"**Funder:** {grant.funder}")
                
                # Display PI information
                if grant.principal_investigators:
                    pi_names = [f"{pi.given_name} {pi.family_name}" for pi in grant.principal_investigators]
                    st.markdown(f"**Principal Investigators:** {', '.join(pi_names)}")
                
                # Display dates if available
                date_info = []
                if grant.start_date:
                    date_info.append(f"Start: {grant.start_date.strftime('%Y-%m-%d')}")
                if grant.end_date:
                    date_info.append(f"End: {grant.end_date.strftime('%Y-%m-%d')}")
                if date_info:
                    st.markdown(f"**Project Period:** {' to '.join(date_info)}")
                
                # Display abstract if available
                if grant.abstract:
                    with st.expander("Abstract"):
                        st.markdown(grant.abstract)
                
            with cols[1]:
                # Display financial information if available
                if grant.amount is not None:
                    currency = grant.currency or 'USD'
                    st.markdown(f"**Amount:** {currency} {grant.amount:,.2f}")
                if grant.year:
                    st.markdown(f"**Fiscal Year:** {grant.year}")
                if grant.is_active is not None:
                    status = "Active" if grant.is_active else "Inactive"
                    st.markdown(f"**Status:** {status}")
                
                # Display keywords if available
                if grant.keywords:
                    st.markdown("**Keywords:**")
                    for keyword in grant.keywords:
                        st.markdown(f"- {keyword}")
#         grants_by_funder = researcher.get_grants_by_funder()
        
#         # Display grants for each funder group
#         for funder, grants in grants_by_funder.items():
#             st.subheader(funder)
#             for grant in grants:
#                 # Create expander title using project title or number
#                 title_part = grant.project_title if grant.project_title else f"Project {grant.project_num}"
#                 expander_title = f"{title_part[:100]}{'...' if len(title_part) > 100 else ''}"
                
#                 with st.expander(expander_title):
#                     st.markdown(f"**Project Number**: {grant.project_num}")
#                     if grant.funder:
#                         st.markdown(f"**Funder**: {grant.funder}")
#                     if grant.pi_name:
#                         st.markdown(f"**PI**: {grant.pi_name}")
#                     if grant.abstract_text:
#                         st.markdown("**Abstract**")
#                         st.markdown(f"> {grant.abstract_text[:500]}..." if len(grant.abstract_text) > 500 else f"> {grant.abstract_text}")

def render_grants_tab():
    """Render the grants tab content"""
    grants_container = st.container()
    with grants_container:
        st.subheader("💰 Research Grants")
        
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
    print(f"Current processing state: {st.session_state.processing_state}")
    print(f"Publications loaded: {st.session_state.publications_loaded}")
    
    if st.session_state.processing_state == "fetch_researcher":
        with researcher_container:
            with st.spinner("Fetching researcher information..."):
                researcher = fetch_researcher_by_orcid(st.session_state.orcid)
                st.session_state.researcher = researcher
                st.session_state.processing_state = "fetch_publications"
                print("Transition to fetch_publications state")
                st.rerun()
    
    elif st.session_state.processing_state == "fetch_publications":
        with publications_container:
            with st.spinner("Fetching publications..."):
                researcher = fetch_publications(st.session_state.researcher)
                st.session_state.researcher = researcher
                
                print(f"Publications count: {len(researcher.publications)}")
                if not researcher.publications:
                    st.session_state.publications_loaded = True
                    st.session_state.processing_state = "fetch_grants"
                    print("No publications found, transition to fetch_grants state")
                else:
                    st.session_state.processing_state = "process_papers"
                    print("Publications found, transition to process_papers state")
                st.rerun()
    
    elif st.session_state.processing_state == "process_papers":
        if st.session_state.researcher.publications:
            with organisms_container:
                with st.spinner("Processing publications to extract organisms..."):
                    print("Starting async processing of papers")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(process_papers_async())
                        st.session_state.publications_loaded = True
                        st.session_state.processing_state = "fetch_grants"
                        print("Papers processed, transition to fetch_grants state")
                        st.rerun()
                    finally:
                        loop.close()
        else:
            no_publications_message = "We didn't find any publications associated with the researcher's ORCID"
            for container in [publications_container, organisms_container]:
                with container:
                    st.info(no_publications_message)
            st.session_state.publications_loaded = True
            st.session_state.processing_state = "complete"
            print("No publications found, transition to complete state")
            st.rerun()
    
    elif st.session_state.processing_state == "fetch_grants":
        with grants_container:
            with st.spinner("Fetching grants information..."):
                researcher = st.session_state.researcher
                researcher = fetch_grants(researcher)
                st.session_state.researcher = researcher
                st.session_state.grants_loaded = True
                st.session_state.processing_state = "complete"
                st.rerun()

def main():
    """Main function to run the Streamlit app"""
    # Set up page config
    setup_page_config()
    
    # Set up page style
    setup_page_style()
    
    # Render header
    render_header()
    
    # Render sidebar
    orcid, search_clicked = render_sidebar()
    
    # Initialize session state
    initialize_session_state()
    
    # Handle search button click
    if search_clicked and orcid:
        st.session_state.orcid = orcid
        st.session_state.processing_state = "fetch_researcher"
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Profile", "Publications", "Grants"])
    
    with tab1:
        # Container for researcher info
        researcher_container = st.container()
        with researcher_container:
            # Display researcher info if available
            if st.session_state.researcher:
                display_researcher_info(st.session_state.researcher)
    
    with tab2:
        # Render publications tab
        publications_container, organisms_container = render_publications_tab()
    
    with tab3:
        # Render grants tab
        grants_container = render_grants_tab()
    
    # Handle the processing state machine
    handle_processing_state(
        researcher_container,
        publications_container,
        organisms_container,
        grants_container
    )

if __name__ == "__main__":
    main()