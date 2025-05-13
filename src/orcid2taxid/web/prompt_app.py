import time
import os
import sys
import subprocess
import atexit
import json
from typing import Dict, Any
import asyncio

import requests
import streamlit as st
from orcid2taxid.llm.extractors.customer_search import search_customer_information

@st.cache_data()  # Cache for 1 hour
def fetch_researcher_data(orcid: str) -> Dict[str, Any]:
    """Fetch researcher data from the API with caching"""
    response = requests.get(f"http://localhost:8000/researcher/{orcid}", timeout=180)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

def filter_json_by_fields(data: Dict[str, Any], selected_fields: Dict[str, Any]) -> Dict[str, Any]:
    """Filter JSON data based on selected fields"""
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if key in selected_fields:
            if isinstance(selected_fields[key], dict):
                if isinstance(value, dict):
                    result[key] = filter_json_by_fields(value, selected_fields[key])
                elif isinstance(value, list):
                    result[key] = [filter_json_by_fields(item, selected_fields[key]) for item in value]
                else:
                    result[key] = value
            elif selected_fields[key]:  # If it's a boolean and True
                result[key] = value
    return result

# Start the FastAPI server as a subprocess
def start_api_server():
    api_path = os.path.join(os.path.dirname(__file__), "api.py")
    return subprocess.Popen([sys.executable, api_path], 
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Start the server when the app loads
if 'api_process' not in st.session_state:
    st.session_state.api_process = start_api_server()
    # Give the server a moment to start
    time.sleep(2)

st.title("ROSE Scout API Interface")

# Sidebar for field selection
st.sidebar.title("Select Fields to Display")

# Define the field structure
root_fields = {
    "researcher_id": True,
    "educations": True,
    "employments": True,
    "external_references": True,
    "publications": True,
    "grants": True,
    "description": False,
}

nested_fields = {
    "publications": {
        "title": True,
        "publication_date": True,
        "journal_name": True,
        "doi": True,
        "organisms": True,
        "authors": False
    },
    "grants": {
        "title": True,
        "funder": True,
        "start_date": True,
        "end_date": True,
        "amount": True
    }
}

# Create checkboxes for each field
selected_fields = {}

st.sidebar.markdown("## Root Fields")
for field, value in root_fields.items():
    selected_fields[field] = st.sidebar.checkbox(field, value=value, key=field)

st.sidebar.markdown("## Nested Fields")
for field, subfields in nested_fields.items():
    with st.sidebar.expander(f"**{field.title()}**"):
        # Only initialize if not already set
        subfield_dict = {}
        for subfield, default in subfields.items():
            subfield_dict[subfield] = st.checkbox(
                f"{field}.{subfield}",
                value=default,
                key=f"{field}.{subfield}"
            )
        if field not in selected_fields:
            selected_fields[field] = subfield_dict

# Create tabs
tab1, tab2 = st.tabs(["Researcher Information", "Customer Search"])

with tab1:

    # Input for ORCID
    orcid = st.text_input("Enter ORCID ID", placeholder="e.g., 0000-0000-0000-0000")

    # Initialize session state for buttons and ORCID tracking
    if 'get_researcher_info' not in st.session_state:
        st.session_state.get_researcher_info = False
    if 'start_customer_search' not in st.session_state:
        st.session_state.start_customer_search = False
    if 'last_orcid' not in st.session_state:
        st.session_state.last_orcid = None

    # Check if ORCID has changed
    if orcid != st.session_state.last_orcid:
        st.session_state.get_researcher_info = False
        st.session_state.last_orcid = orcid

    # Create a row for the buttons
    col1, col2 = st.columns([1, 3])
    
    # Button to trigger researcher info fetch
    with col1:
        st.button("Get Researcher Info", key="researcher_info_button", on_click=lambda: setattr(st.session_state, 'get_researcher_info', True))
    
    # Button to trigger customer search
    with col2:
        st.button("Start Customer Search", key="customer_search_button", on_click=lambda: setattr(st.session_state, 'start_customer_search', True))

    # Display researcher info if button was clicked
    if st.session_state.get_researcher_info:
        if orcid:
            try:
                # Fetch data with caching
                data = fetch_researcher_data(orcid)
                # Filter and display the JSON response
                filtered_data = filter_json_by_fields(data, selected_fields)
                st.json(filtered_data)
                
                # Store the filtered data in session state for customer search
                st.session_state.filtered_data = filtered_data
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the API server. Make sure it's running on http://localhost:8000")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.info("Please enter an ORCID ID to see the researcher information")

with tab2:
    st.header("Customer Search Results")
    
     # Run customer search if button was clicked
    if st.session_state.start_customer_search:
        if 'filtered_data' in st.session_state:
            try:
                # Convert the filtered data to a string representation
                data_str = json.dumps(st.session_state.filtered_data, indent=2)
                
                # Run the customer search
                with st.spinner("Searching customer information..."):
                    result = asyncio.run(search_customer_information(data_str))
                    # Store the result in session state for display in tab2
                    st.session_state.customer_search_result = result.model_dump()
            except Exception as e:
                st.error(f"An error occurred during customer search: {str(e)}")
        else:
            st.info("Please fetch researcher information first using the 'Get Researcher Info' button")
        # Reset the button state
        st.session_state.start_customer_search = False
        
    if 'customer_search_result' in st.session_state:
        st.json(st.session_state.customer_search_result)
    else:
        st.info("No customer search results available. Please run a customer search from the Researcher Information tab.")

# Cleanup when the app is closed
def cleanup():
    if 'api_process' in st.session_state:
        st.session_state.api_process.terminate()
        st.session_state.api_process.wait()

# Register the cleanup function
atexit.register(cleanup)
