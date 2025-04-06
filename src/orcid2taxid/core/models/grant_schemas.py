from pydantic import Field
from typing import Optional, List, Dict
from datetime import datetime
from orcid2taxid.core.models.base_schemas import DatetimeSerializableBaseModel


class GrantMetadata(DatetimeSerializableBaseModel):
    """Represents comprehensive grant information from NIH Reporter or Europe PMC"""
    # Core grant information
    project_title: str = Field(description="Title of the research project")
    project_num: str = Field(description="Grant/project identifier")
    funder: Optional[str] = Field(description="Funding agency/organization")
    
    # Financial information (mainly from NIH Reporter)
    fiscal_year: Optional[int] = Field(description="Fiscal year of the grant")
    award_amount: Optional[float] = Field(description="Total award amount")
    direct_costs: Optional[float] = Field(description="Direct costs of the project")
    indirect_costs: Optional[float] = Field(description="Indirect costs of the project")
    
    # Temporal information
    project_start_date: Optional[datetime] = Field(description="Project start date")
    project_end_date: Optional[datetime] = Field(description="Project end date")
    
    # Organization information
    organization: Dict[str, str] = Field(
        default_factory=dict,
        description="Organization details including name, city, state, country"
    )
    
    # Principal Investigator information
    pi_name: Optional[str] = Field(description="Name of the Principal Investigator")
    pi_profile_id: Optional[str] = Field(description="NIH profile ID of the PI")
    
    # Project details
    abstract_text: Optional[str] = Field(description="Project abstract")
    project_terms: List[str] = Field(
        default_factory=list,
        description="Project terms/keywords"
    )
    
    # Funding mechanism details (mainly from NIH Reporter)
    funding_mechanism: Optional[str] = Field(description="Type of funding mechanism")
    activity_code: Optional[str] = Field(description="NIH activity code")
    award_type: Optional[str] = Field(description="Type of award")
    
    # Study section information (NIH Reporter specific)
    study_section: Optional[str] = Field(description="NIH study section name")
    study_section_code: Optional[str] = Field(description="NIH study section code")
    
    # Additional metadata
    last_updated: Optional[datetime] = Field(description="Last update timestamp")
    is_active: Optional[bool] = Field(description="Whether the grant is currently active")
    is_arra: Optional[bool] = Field(description="Whether funded by ARRA (American Recovery and Reinvestment Act)")
    covid_response: Optional[str] = Field(description="COVID-19 response funding category if applicable")
    
    # Europe PMC specific fields
    grant_type: Optional[str] = Field(description="Type of grant (e.g., research grant, fellowship)")
    grant_status: Optional[str] = Field(description="Current status of the grant (e.g., active, completed)")
    grant_currency: Optional[str] = Field(description="Currency of the grant amount")
    grant_country: Optional[str] = Field(description="Country where the grant was awarded")
    grant_department: Optional[str] = Field(description="Department or division within the funding organization")
    grant_institution: Optional[str] = Field(description="Institution where the grant was awarded")
