from typing import Optional, List
from datetime import datetime
from pydantic import Field
from orcid2taxid.core.models.base_schemas import DatetimeSerializableBaseModel, ResearcherProfile
from orcid2taxid.core.models.grant_schemas import GrantMetadata
from orcid2taxid.core.models.extraction_schemas import PaperClassificationMetadata
from orcid2taxid.core.models.integrations.ncbi_schemas import OrganismMention


class PublicationRecord(DatetimeSerializableBaseModel):
    """Represents metadata for a scientific publication"""
    title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[datetime] = None
    journal_name: Optional[str] = None
    journal_issn: Optional[str] = None
    authors: List[ResearcherProfile] = Field(default_factory=list)
    source: Optional[str] = None
    
    full_text_url: Optional[str] = None
    citation_count: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    funding_info: List[GrantMetadata] = Field(default_factory=list)
    organisms: List[OrganismMention] = Field(default_factory=list)
    classification: Optional[PaperClassificationMetadata] = None