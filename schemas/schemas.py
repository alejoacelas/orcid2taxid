from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional
from datetime import date

class AuthorAffiliation(BaseModel):
    """Represents an institution affiliation for an author"""
    institution_name: str
    department: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
class AuthorMetadata(BaseModel):
    """Represents author information from ORCID or other sources"""
    full_name: str
    orcid: Optional[str] = None
    affiliations: List[AuthorAffiliation] = Field(default_factory=list)

class Author(BaseModel):
    """Simplified author information as it appears in a publication"""
    full_name: str
    orcid: Optional[str] = None
    affiliations: List[str] = Field(default_factory=list)

class PaperMetadata(BaseModel):
    """Represents a scientific publication's metadata"""
    title: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    publication_date: Optional[date] = None
    journal: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    full_text_url: Optional[HttpUrl] = None
    pdf_url: Optional[HttpUrl] = None
    repository_source: str = Field(description="Source repository: 'pubmed', 'biorxiv', etc.")
    
class OrganismMention(BaseModel):
    """Represents a single organism mention found in text"""
    name: str
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the organism identification"
    )
    source: str = Field(
        description="Source of identification: 'gnf', 'llm', or 'gnf+llm'"
    )
    context: Optional[str] = Field(
        description="Surrounding text context where the organism was mentioned"
    )
    
class OrganismList(BaseModel):
    """Collection of organisms found in a publication"""
    paper_id: str = Field(description="DOI, PMID, or other unique identifier")
    organisms: List[OrganismMention] = Field(default_factory=list)
    taxids: Dict[str, int] = Field(
        default_factory=dict,
        description="Mapping of scientific names to NCBI TAXIDs"
    )
    extraction_method: str = Field(
        description="Method used: 'full_text' or 'abstract_only'"
    ) 