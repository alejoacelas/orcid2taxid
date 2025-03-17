from typing import List, Dict, Optional
from pydantic import BaseModel, Field

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
    given_name: Optional[str] = None
    family_name: Optional[str] = None
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
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    full_name: str
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

class NCBITaxonomyInfo(BaseModel):
    """Represents comprehensive taxonomy information from NCBI"""
    taxid: int = Field(description="NCBI Taxonomy ID")
    scientific_name: str = Field(description="Scientific name of the organism")
    rank: Optional[str] = Field(description="Taxonomic rank (e.g., species, genus)")
    division: Optional[str] = Field(description="Division/domain (e.g., Bacteria, Viruses)")
    common_name: Optional[str] = Field(description="Common name if available")
    lineage: Optional[List[str]] = Field(description="Full taxonomic lineage")
    synonyms: Optional[List[str]] = Field(description="List of synonyms")
    genetic_code: Optional[str] = Field(description="Genetic code used by the organism")
    mito_genetic_code: Optional[str] = Field(description="Mitochondrial genetic code if applicable")
    is_parasite: Optional[bool] = Field(description="Whether the organism is parasitic")
    is_pathogen: Optional[bool] = Field(description="Whether the organism is pathogenic")
    host_taxid: Optional[int] = Field(description="TaxID of the primary host if parasitic/pathogenic")
    host_scientific_name: Optional[str] = Field(description="Scientific name of the primary host")

class OrganismMention(BaseModel):
    """Represents a mention of an organism in text"""
    original_name: str = Field(description="Original organism name as found in text")
    searchable_name: str = Field(description="Searchable organism name for NCBI database")
    context: Optional[str] = Field(description="Context in which the organism was mentioned")
    confidence: Optional[float] = Field(description="Confidence score of the extraction")
    justification: Optional[str] = Field(description="Explanation of why this organism was included")
    taxonomy_info: Optional[NCBITaxonomyInfo] = Field(description="NCBI taxonomy information if available")

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