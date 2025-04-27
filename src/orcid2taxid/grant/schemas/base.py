from typing import Optional, List
from datetime import datetime
from pydantic import Field
from orcid2taxid.shared.schemas import (
    DatetimeSerializableBaseModel, ResearcherProfile
)
from orcid2taxid.grant.schemas.nih import NIHProject

class GrantRecord(DatetimeSerializableBaseModel):
    """Represents comprehensive grant information from NIH Reporter or Europe PMC"""
    # Core grant information
    id: str = Field(description="Grant/project identifier")
    title: Optional[str] = Field(None, description="Title of the research project")
    funder: Optional[str] = Field(None, description="Funding agency/organization")
    
    # Financial information (mainly from NIH Reporter)
    year: Optional[int] = Field(None, description="Fiscal year of the grant")
    amount: Optional[str] = Field(None, description="Total award amount, including currency denomination")
    
    # Temporal information
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    
    # Organization information
    recipient: Optional[str] = Field(None, description="Recipient organization")
    
    # Principal Investigator information
    principal_investigator: Optional[ResearcherProfile] = Field(None, description="Principal Investigator information")
    
    # Project details
    abstract: Optional[str] = Field(None, description="Project abstract")
    keywords: List[str] = Field(
        default_factory=list,
        description="Project terms/keywords"
    )
    award_type: Optional[str] = Field(None, description="Type of award")

    @classmethod
    def from_nih_project(cls, nih_project: NIHProject) -> "GrantRecord":
        """Create a GrantRecord from an NIH Reporter project"""
        # Extract organization information
        org_data = nih_project.organization or {}
        
        # Extract PI information
        pi_data = nih_project.contact_pi or {}
        pi_name = f"{pi_data.last_name or ''}, {pi_data.first_name or ''}".strip(', ')
        
        # Extract project terms
        project_terms = [term.term for term in nih_project.project_terms if term.term]
        
        # Create GrantRecord object
        return cls(
            title=nih_project.title,
            id=nih_project.project_num,
            funder='NIH',
            year=nih_project.fiscal_year,
            amount=nih_project.award_amount,
            direct_costs=nih_project.direct_costs,
            indirect_costs=nih_project.indirect_costs,
            start_date=nih_project.start_date,
            end_date=nih_project.end_date,
            recipient=org_data.name if org_data else None,
            principal_investigator=pi_name,
            abstract=nih_project.abstract,
            project_terms=project_terms,
            award_type=nih_project.award_type,
            study_section=nih_project.study_section.name if nih_project.study_section else None,
            study_section_code=nih_project.study_section.code if nih_project.study_section else None,
            last_updated=nih_project.last_updated,
            is_active=nih_project.is_active,
            is_array_funded=nih_project.is_array_funded,
            covid_response=nih_project.covid_response,
            # Add required fields with appropriate values
            grant_type=nih_project.award_type or 'research',  # Default to research if not specified
            grant_status='active' if nih_project.is_active else 'completed',
            grant_currency='USD',  # NIH grants are always in USD
            grant_country=org_data.country if org_data else 'United States',
            grant_department=org_data.department if org_data else None,
            grant_institution=org_data.name if org_data else None
        )