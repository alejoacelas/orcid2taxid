from typing import Optional, List
from datetime import datetime
from pydantic import Field, field_validator
from orcid2taxid.shared.schemas import (
    DatetimeSerializableBaseModel, ResearcherID
)
from orcid2taxid.shared.utils import ensure_datetime
from orcid2taxid.grant.schemas.nih import NIHProject

class GrantRecord(DatetimeSerializableBaseModel):
    """Represents comprehensive grant information from NIH Reporter or Europe PMC"""
    # Core grant information
    id: str = Field(description="Grant/project identifier")
    title: Optional[str] = Field(None, description="Title of the research project")
    funder: Optional[str] = Field(None, description="Funding agency/organization")
    
    # Financial information (mainly from NIH Reporter)
    year: Optional[int] = Field(None, description="Fiscal year of the grant")
    amount: Optional[float] = Field(None, description="Total award amount")
    currency: Optional[str] = Field(None, description="Currency of the award")
    
    # Temporal information
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    
    # Validators to ensure datetime objects
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def ensure_datetime_objects(cls, v):
        return ensure_datetime(v)
    
    # Organization information
    recipient: Optional[str] = Field(None, description="Recipient organization")
    
    # Principal Investigators information
    principal_investigators: List[ResearcherID] = Field(
        default_factory=list,
        description="List of Principal Investigators information"
    )
    
    # Project details
    abstract: Optional[str] = Field(None, description="Project abstract")
    keywords: List[str] = Field(
        default_factory=list,
        description="Project terms/keywords"
    )
    description: Optional[str] = Field(None, description="Project description")
    is_active: Optional[bool] = Field(None, description="Whether the grant is active")
    award_type: Optional[str] = Field(None, description="Type of award")
    
    # Source information
    source_doi: Optional[str] = Field(None, description="DOI of the publication this grant was detected from")

    @classmethod
    def from_nih_project(cls, nih_project: NIHProject) -> "GrantRecord":
        """Create a GrantRecord from an NIH Reporter project"""
        # Extract organization information
        org_data = nih_project.organization or {}
        
        # Extract PI information - handle updated structure with principal_investigators list
        principal_investigators = []
        
        if nih_project.principal_investigators:
            for pi in nih_project.principal_investigators:
                researcher_name = ResearcherID(
                    given_name=pi.first_name,
                    family_name=pi.last_name,
                    credit_name=pi.full_name
                )
                principal_investigators.append(researcher_name)
        elif nih_project.contact_pi_name:
            # Handle legacy format with just a name string
            name_parts = nih_project.contact_pi_name.split(',', 1)
            if len(name_parts) == 2:
                family_name, given_name = name_parts[0].strip(), name_parts[1].strip()
            else:
                family_name, given_name = name_parts[0].strip(), ""
                
            researcher_name = ResearcherID(
                given_name=given_name,
                family_name=family_name,
                credit_name=nih_project.contact_pi_name
            )
            principal_investigators.append(researcher_name)
        
        # Construct recipient field with organization details
        recipient_parts = []
        if org_data:
            if org_data.name:
                recipient_parts.append(org_data.name)
            if org_data.department:
                recipient_parts.append(org_data.department)
            if org_data.country:
                recipient_parts.append(org_data.country)
        recipient = ", ".join(recipient_parts) if recipient_parts else None
        
        # Extract terms/keywords from pref_terms (preferred terms)
        terms = []
        if nih_project.pref_terms:
            terms = [term.strip() for term in nih_project.pref_terms.split(';') if term.strip()]
        
        # Get agency info
        agency_info = nih_project.agency_ic_admin.name if nih_project.agency_ic_admin else 'NIH'
        
        # Create GrantRecord object
        return cls(
            id=nih_project.project_num,
            title=nih_project.title,
            funder=agency_info,
            year=nih_project.fiscal_year,
            amount=nih_project.award_amount if nih_project.award_amount is not None else None,
            currency="USD",
            start_date=nih_project.start_date,
            end_date=nih_project.end_date,
            recipient=recipient,
            principal_investigators=principal_investigators,
            abstract=nih_project.abstract,
            keywords=terms,
            award_type=nih_project.award_type or 'research',
            description=f"### Public Health Relevance: \n{nih_project.phr_text}",
            is_active=nih_project.is_active,
        )