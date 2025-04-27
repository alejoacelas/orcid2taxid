from typing import Optional, List
from datetime import datetime
from pydantic import Field
from orcid2taxid.shared.schemas import (
    DatetimeSerializableBaseModel, ResearcherProfile
)

class GrantRecord(DatetimeSerializableBaseModel):
    """Represents comprehensive grant information from NIH Reporter or Europe PMC"""
    # Core grant information
    id: str = Field(description="Grant/project identifier")
    title: Optional[str] = Field(description="Title of the research project")
    funder: Optional[str] = Field(description="Funding agency/organization")
    
    # Financial information (mainly from NIH Reporter)
    year: Optional[int] = Field(description="Fiscal year of the grant")
    amount: Optional[str] = Field(description="Total award amount, including currency denomination")
    
    # Temporal information
    start_date: Optional[datetime] = Field(description="Project start date")
    end_date: Optional[datetime] = Field(description="Project end date")
    
    # Organization information
    recipient: Optional[str] = Field(
        description="Recipient organization"
    )
    
    # Principal Investigator information
    principal_investigator: Optional[ResearcherProfile] = Field(description="Principal Investigator information")
    
    # Project details
    abstract: Optional[str] = Field(description="Project abstract")
    keywords: List[str] = Field(
        default_factory=list,
        description="Project terms/keywords"
    )
    award_type: Optional[str] = Field(description="Type of award")