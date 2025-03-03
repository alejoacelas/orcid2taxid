from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional

class AuthorAffiliation(BaseModel):
    """Represents an author's affiliation with an institution"""
    institution_name: str
    department: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None  # ISO format YYYY-MM-DD
    end_date: Optional[str] = None    # ISO format YYYY-MM-DD
    visibility: Optional[str] = None

class ExternalId(BaseModel):
    """Represents an external identifier with its value, URL and metadata"""
    value: str
    url: Optional[str] = None
    relationship: Optional[str] = None
    visibility: Optional[str] = None

class ResearcherUrl(BaseModel):
    """Represents a researcher's URL (e.g. personal website, LinkedIn)"""
    name: Optional[str] = None
    url: str
    visibility: Optional[str] = None

class EmailInfo(BaseModel):
    """Represents an email address with its metadata"""
    address: str
    verified: bool = False
    primary: bool = False
    visibility: Optional[str] = None

class CountryInfo(BaseModel):
    """Represents a country with its metadata"""
    code: str
    visibility: Optional[str] = None

class AuthorMetadata(BaseModel):
    """Represents comprehensive author information from ORCID"""
    orcid: str
    full_name: str
    credit_name: Optional[str] = None
    alternative_names: List[str] = Field(default_factory=list)
    biography: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    researcher_urls: List[ResearcherUrl] = Field(default_factory=list)
    email: Optional[EmailInfo] = None
    country: Optional[CountryInfo] = None
    external_ids: Dict[str, ExternalId] = Field(default_factory=dict)
    education: List[AuthorAffiliation] = Field(default_factory=list)
    affiliations: List[AuthorAffiliation] = Field(default_factory=list)
    last_modified: Optional[int] = None

class Author(BaseModel):
    """Simplified author information as it appears in a publication"""
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    orcid: Optional[str] = None
    email: Optional[str] = None
    affiliations: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    sequence: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)

class FundingInfo(BaseModel):
    """Represents funding information for a publication"""
    name: Optional[str] = None
    funder: Optional[str] = None
    grant_number: Optional[str] = None

class JournalInfo(BaseModel):
    """Detailed journal information"""
    title: Optional[str] = None
    issn: Optional[str] = None
    eissn: Optional[str] = None
    nlm_id: Optional[str] = None
    iso_abbreviation: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None

class PaperMetadata(BaseModel):
    """Represents metadata for a scientific publication"""
    title: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    publication_date: Optional[str] = None  # ISO format YYYY-MM-DD
    journal: Optional[str] = None
    journal_info: Optional[JournalInfo] = None
    abstract: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    repository_source: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    full_text_urls: List[str] = Field(default_factory=list)
    citation_count: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    funding_info: List[FundingInfo] = Field(default_factory=list)
    external_ids: Dict[str, ExternalId] = Field(default_factory=dict)
    language: Optional[str] = None
    country: Optional[str] = None
    visibility: Optional[str] = None
    publication_status: Optional[str] = None
    is_open_access: bool = False
    has_pdf: bool = False

class OrganismMention(BaseModel):
    """Represents a mention of an organism in text"""
    name: str
    taxid: Optional[str] = None
    scientific_name: Optional[str] = None
    rank: Optional[str] = None
    division: Optional[str] = None
    confidence: Optional[float] = None
    context: Optional[str] = None

class OrganismList(BaseModel):
    """Represents a list of organisms associated with a publication"""
    paper_metadata: PaperMetadata
    organisms: List[OrganismMention] = Field(default_factory=list)
    taxids: Dict[str, int] = Field(
        default_factory=dict,
        description="Mapping of scientific names to NCBI TAXIDs"
    )
    extraction_method: str = Field(
        description="Method used: 'full_text' or 'abstract_only'"
    ) 