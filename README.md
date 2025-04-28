# ORCID2TAXID Mapper

## TODO

[] Check which fields should be required from integration API responses
[] Create comprehensive repo planning to guide the AI
[] Do tests well
[] Figure out how to search by name in EPMC and NIH

## Overview

ORCID2TAXID works by analyzing a researcher's publication history through multiple sources and extracting organism mentions from their publications which are mapped to TAXIDs using NCBI's e-search API.

This project came out from the idea introduced by Tessa Alexanian and Max Lagenkamp in this [EA Forum post](https://forum.effectivealtruism.org/posts/RwMpnHwqhTZ2rrwbr/five-tractable-biosecurity-projects-you-could-start-tomorrow).

## Repository Structure

```
orcid2taxid/
├── src/
│   └── orcid2taxid/
│       ├── web/         # Web interface and API
│       ├── core/        # Core functionality modules
│       ├── integrations/# External service integrations
│       └── analysis/    # Analysis and processing modules
├── tests/               # Test suite
├── notebooks/           # Jupyter notebooks for development
├── .streamlit/          # Streamlit configuration
├── requirements.txt     # Project dependencies
└── setup.py            # Package installation configuration
```

## Technical Implementation Details

### 1. Component Architecture

The system is organized into several specialized components:

- Web Interface: Streamlit-based UI for easy access
- API Layer: FastAPI-based REST API
- Core Components: Publication retrieval and organism detection
- Analysis: Text processing and organism name extraction
- Integrations: External APIs (ORCID, NCBI, etc.)

### 2. Publication Collection and Processing

The system implements a multi-stage process:

1. Retrieves publications from ORCID and other sources
2. Processes text to identify organism mentions
3. Maps identified organisms to NCBI TAXIDs
4. Provides results through both web UI and API

### 3. Organism Detection Strategy

The system uses a combination of techniques to detect organisms:

1. Text Analysis
   - Processes publication text and abstracts
   - Uses advanced NLP to identify organism mentions
   - Standardizes organism names

2. TAXID Mapping
   - Maps identified organisms to NCBI taxonomy IDs
   - Validates and verifies taxonomic classifications
   - Maintains mapping accuracy

### 4. TAXID Mapping

Converts organism names to NCBI TAXIDs:

- Iterates through detected organisms
- Uses `NCBITaxIDLookup` to get corresponding TAXIDs
- Maintains mapping between names and IDs

### 5. Result Structure

Organizes results using defined schemas:

- `OrganismMention`: Individual organism references with metadata
- `OrganismList`: Paper-level collection of organisms and TAXIDs
- Includes confidence scores and extraction method information

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/orcid2taxid.git
cd orcid2taxid

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`

# Install dependencies and package
pip install -r requirements.txt
```

## Usage

### Web Interface

Run the Streamlit app locally:

```bash
streamlit run src/orcid2taxid/web/app.py
```

### API

Start the FastAPI server:

```bash
uvicorn orcid2taxid.web.api:app --reload --host 0.0.0.0 --port 8000
```

Access the API at:

- API endpoint: http://localhost:8000/orcid2taxid/{orcid_id}
- API documentation: http://localhost:8000/docs

### Example API Call

```bash
# Get organism information for an ORCID
curl http://localhost:8000/orcid2taxid/0009-0009-2183-7559

# Limit results
curl "http://localhost:8000/orcid2taxid/0009-0009-2183-7559?max_results=5"
```

## Environment Setup

Create a `.env` file with required API keys:

```
ANTHROPIC_API_KEY=your_key_here
```

## Deployment on Streamlit Cloud

1. Connect your GitHub account at [share.streamlit.io](https://share.streamlit.io)
2. Deploy this repository with:
   - Main file path: `src/orcid2taxid/web/app.py`
3. Add your `ANTHROPIC_API_KEY` to the app's secrets in Streamlit Cloud settings

That's it! The app will be accessible via the Streamlit Cloud URL provided.
