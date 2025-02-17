# ORCID2TAXID Mapper

## Overview

ORCID2TAXID works by analyzing a researcher's publication history through multiple sources and extracting organism mentions from their publications which are mapped to TAXIDs using NCBI's e-search API. 

## Technical Implementation Details

### 1. Component Initialization
The system initializes several specialized components:
- `OrcidFetcher`: Retrieves researcher information and publications from ORCID
- Publication repositories: `PubmedFetcher` and `BiorxivFetcher`
- `UnpaywallFetcher`: Obtains full-text access to papers if available
- `GnfFinder`: Uses GlobalNames.org API for organism name detection
- `LLMAnalyzer`: Uses Claude 3.5 for text analysis
- `NCBITaxIDLookup`: Maps organism names to NCBI TAXIDs

### 2. Publication Collection and Filtering
The system implements a multi-stage filtering process:
1. Fetches author metadata and verified publications from ORCID
2. Collects publications from multiple sources (PubMed, bioRxiv)
3. Applies two filtering steps:
   - `DuplicateFilter`: Removes duplicate publications
   - `AuthorVerificationFilter`: Verifies authorship with a confidence threshold

### 3. Organism Detection Strategy
Implements a fallback strategy for organism detection:
1. Primary approach: Full-text
   - Uses Unpaywall to get PDF access
   - Processes full text with GNF
   - Standardizes organism names using an LLM

2. Fallback approach: Abstract-only
   - Uses LLM to analyze abstract text
   - Standardizes organism names using an LLM

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

## Usage

```bash
python main.py <ORCID>
```

Replace `<ORCID>` with the researcher's ORCID identifier (e.g., "0000-0002-1825-0097").

## Output

The tool returns a list of `OrganismList` objects containing:
- Paper identifiers
- Detected organisms
- Corresponding TAXIDs
- Confidence scores
- Extraction methods used
