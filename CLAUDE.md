# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test module
pytest tests/integrations/test_grant_nih.py

# Run with async support (configured in pytest.ini)
pytest -v
```

### Web Applications
```bash
# Run Streamlit app (main web interface)
streamlit run src/orcid2taxid/web/app.py

# Run FastAPI server (REST API)
uvicorn orcid2taxid.web.api:app --reload --host 0.0.0.0 --port 8000
```

### Package Installation
```bash
# Install in development mode
pip install -r requirements.txt
```

## Architecture Overview

### Core Data Flow
The system follows a pipeline architecture:
1. **Researcher Profile** → `researcher/services.py:get_customer_profile()` fetches ORCID data
2. **Publication Collection** → `publication/integrations/epmc.py` retrieves papers from Europe PMC
3. **Organism Extraction** → `llm/extractors/organism_mention.py` uses LLM (Gemini 2.0 Flash) to extract organism names from abstracts
4. **Taxonomy Mapping** → `taxonomy/integrations/ncbi.py` maps organisms to NCBI taxonomy IDs
5. **Grant Integration** → `grant/integrations/nih.py` fetches NIH/NSF grants associated with the researcher

### Service Layer Architecture
- **Domain Modules**: Each domain (`researcher/`, `publication/`, `grant/`, `taxonomy/`) has:
  - `integrations/` - External API clients
  - `schemas/` - Pydantic models for data validation  
  - `services.py` - Business logic coordination
  - `exceptions.py` - Domain-specific errors

### LLM Integration
- Uses `instructor` library for structured output from Gemini models
- Prompts stored in `llm/prompts/` with context injection
- Rate limiting via `aiolimiter` (100 requests/minute)
- Organism extraction uses pathogen-specific prompts for biosecurity focus

### Shared Infrastructure
- `shared/schemas/base.py` contains core models like `ResearcherID` and `InstitutionalAffiliation`
- `core/logging.py` provides hierarchical logging with event decorators
- All external integrations are async with structured error handling

### Web Layer
- **API** (`web/api.py`): FastAPI endpoints for programmatic access
- **Streamlit App** (`web/app.py`): Interactive web interface with caching and async processing
- Both applications provide researcher profiling with organism identification

## Environment Variables
Required in `.env` file:
- `ANTHROPIC_API_KEY`: For LLM-based organism extraction (uses Gemini via anthropic client)

## Key Integration Points
- **ORCID API**: Researcher profiles, publications, affiliations
- **Europe PMC**: Full-text publication metadata and abstracts  
- **NCBI Taxonomy**: Organism name to TaxID mapping
- **NIH RePORTER**: Research grant data
- **Gemini 2.0 Flash**: Organism mention extraction from scientific text