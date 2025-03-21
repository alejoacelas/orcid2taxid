from typing import List, Dict, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from collections import defaultdict

class CustomBaseModel(BaseModel):
    """Base model with custom JSON serialization configuration"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            set: list
        }
    )

    def model_dump(self, **kwargs):
        """Custom serialization method"""
        return super().model_dump(
            exclude_none=True,
            **kwargs
        )

    def to_json(self, **kwargs):
        """Custom serialization method"""
        return self.model_dump_json(**kwargs)

class AuthorAffiliation(CustomBaseModel):
    """Represents an author's affiliation with an institution"""
    institution_name: str
    department: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ExternalId(CustomBaseModel):
    """Represents an external identifier with its value, URL and metadata"""
    value: str
    url: Optional[str] = None
    relationship: Optional[str] = None

class ResearcherUrl(CustomBaseModel):
    """Represents a researcher's URL (e.g. personal website, LinkedIn)"""
    name: Optional[str] = None
    url: str

class EmailInfo(CustomBaseModel):
    """Represents an email address with its metadata"""
    address: str
    verified: bool = False
    primary: bool = False

class CountryInfo(CustomBaseModel):
    """Represents a country with its metadata"""
    code: str


class Author(CustomBaseModel):
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

class FundingInfo(CustomBaseModel):
    """Represents funding information for a publication"""
    name: Optional[str] = None
    funder: Optional[str] = None
    grant_number: Optional[str] = None

class NCBITaxonomyInfo(CustomBaseModel):
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

class OrganismMention(CustomBaseModel):
    """Represents a mention of an organism in text"""
    original_name: str = Field(description="Original organism name as found in text")
    searchable_name: str = Field(description="Searchable organism name for NCBI database")
    context: Optional[str] = Field(description="Context in which the organism was mentioned")
    confidence: Optional[float] = Field(description="Confidence score of the extraction")
    justification: Optional[str] = Field(description="Explanation of why this organism was included")

class PaperMetadata(CustomBaseModel):
    """Represents metadata for a scientific publication"""
    title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[datetime] = None
    journal_name: Optional[str] = None
    journal_issn: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    full_text_url: Optional[str] = None
    citation_count: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    funding_info: List[FundingInfo] = Field(default_factory=list)
    organisms: List[OrganismMention] = Field(default_factory=list)
    taxids: List[NCBITaxonomyInfo] = Field(default_factory=list)

class ResearcherMetadata(CustomBaseModel):
    """Represents metadata for a researcher"""
    orcid: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[EmailInfo] = None
    
    # Core fields that are always populated from ORCID
    full_name: str
    credit_name: Optional[str] = None
    biography: Optional[str] = None
    researcher_urls: List[ResearcherUrl] = Field(default_factory=list)
    country: Optional[CountryInfo] = None
    last_modified: Optional[datetime] = None
    
    # Fields that can be enriched from publications
    alternative_names: Set[str] = Field(default_factory=set)
    keywords: Set[str] = Field(default_factory=set)
    subjects: Set[str] = Field(default_factory=set)
    journals: Set[str] = Field(default_factory=set)
    external_ids: Dict[str, ExternalId] = Field(default_factory=dict)
    education: List[AuthorAffiliation] = Field(default_factory=list)
    affiliations: List[AuthorAffiliation] = Field(default_factory=list)
    
    # Publications
    publications: List[PaperMetadata] = Field(default_factory=list)
    
    def get_publication_count(self) -> int:
        """Get total number of publications"""
        return len(self.publications)
    
    def get_publications_by_year(self) -> Dict[int, List[PaperMetadata]]:
        """Get publications grouped by year"""
        by_year = defaultdict(list)
        for paper in self.publications:
            if paper.publication_date:
                by_year[paper.publication_date.year].append(paper)
        return dict(by_year)
    
    def get_publications_by_journal(self) -> Dict[str, List[PaperMetadata]]:
        """Get publications grouped by journal"""
        by_journal = defaultdict(list)
        for paper in self.publications:
            if paper.journal_name:
                by_journal[paper.journal_name].append(paper)
        return dict(by_journal)
    
    def get_publications_by_organism(self) -> Dict[str, List[PaperMetadata]]:
        """Get publications grouped by organism"""
        by_organism = defaultdict(list)
        for paper in self.publications:
            for organism in paper.organisms:
                if organism.taxonomy_info:
                    by_organism[organism.taxonomy_info.scientific_name].append(paper)
        return dict(by_organism)
