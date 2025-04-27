from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, AliasPath

class NIHBaseModel(BaseModel):
    """Base model for all NIH Reporter models with shared config"""
    model_config = ConfigDict(
        populate_by_name=True,
        extra='allow'
    )

class NIHOrganization(NIHBaseModel):
    """Organization data from NIH Reporter API"""
    name: str = Field(validation_alias=AliasPath('org_name'))
    city: Optional[str] = Field(None, validation_alias=AliasPath('org_city'))
    state: Optional[str] = Field(None, validation_alias=AliasPath('org_state'))
    country: Optional[str] = Field(None, validation_alias=AliasPath('org_country'))
    department: Optional[str] = Field(None, validation_alias=AliasPath('org_dept'))
    duns: Optional[str] = Field(None, validation_alias=AliasPath('org_duns'))
    zip: Optional[str] = Field(None, validation_alias=AliasPath('org_zip'))
    type: Optional[str] = Field(None, validation_alias=AliasPath('org_type'))
    fips: Optional[str] = Field(None, validation_alias=AliasPath('org_fips'))
    uei: Optional[str] = Field(None, validation_alias=AliasPath('org_uei'))
    ipf: Optional[str] = Field(None, validation_alias=AliasPath('org_ipf'))

class NIHPrincipalInvestigator(NIHBaseModel):
    """Principal Investigator data from NIH Reporter API"""
    first_name: Optional[str] = Field(None, validation_alias=AliasPath('first_name'))
    last_name: Optional[str] = Field(None, validation_alias=AliasPath('last_name'))
    full_name: Optional[str] = Field(None, validation_alias=AliasPath('full_name'))
    email: Optional[str] = Field(None, validation_alias=AliasPath('email'))
    profile_id: Optional[int] = Field(None, validation_alias=AliasPath('profile_id'))

class NIHStudySection(NIHBaseModel):
    """Study Section data from NIH Reporter API"""
    code: Optional[str] = Field(None, validation_alias=AliasPath('study_section_code'))
    name: Optional[str] = Field(None, validation_alias=AliasPath('study_section'))
    flex_code: Optional[str] = Field(None, validation_alias=AliasPath('sra_flex_code'))
    designator_code: Optional[str] = Field(None, validation_alias=AliasPath('sra_designator_code'))
    group_code: Optional[str] = Field(None, validation_alias=AliasPath('group_code'))

class NIHProjectTerm(NIHBaseModel):
    """Project term/keyword from NIH Reporter API"""
    term: str = Field(validation_alias=AliasPath('term'))
    category: Optional[str] = Field(None, validation_alias=AliasPath('category'))

class NIHProject(NIHBaseModel):
    """Raw project data from NIH Reporter API"""
    project_num: str = Field(validation_alias=AliasPath('project_num'))
    title: Optional[str] = Field(None, validation_alias=AliasPath('project_title'))
    abstract: Optional[str] = Field(None, validation_alias=AliasPath('abstract_text'))
    fiscal_year: Optional[int] = Field(None, validation_alias=AliasPath('fiscal_year'))
    award_amount: Optional[float] = Field(None, validation_alias=AliasPath('award_amount'))
    direct_costs: Optional[float] = Field(None, validation_alias=AliasPath('direct_cost_amt'))
    indirect_costs: Optional[float] = Field(None, validation_alias=AliasPath('indirect_cost_amt'))
    start_date: Optional[datetime] = Field(None, validation_alias=AliasPath('project_start_date'))
    end_date: Optional[datetime] = Field(None, validation_alias=AliasPath('project_end_date'))
    organization: Optional[NIHOrganization] = Field(None, validation_alias=AliasPath('organization'))
    contact_pi: Optional[NIHPrincipalInvestigator] = Field(None, validation_alias=AliasPath('contact_pi'))
    study_section: Optional[NIHStudySection] = Field(None, validation_alias=AliasPath('study_section'))
    project_terms: List[NIHProjectTerm] = Field(default_factory=list, validation_alias=AliasPath('project_terms'))
    award_type: Optional[str] = Field(None, validation_alias=AliasPath('award_type'))
    funding_mechanism: Optional[str] = Field(None, validation_alias=AliasPath('funding_mechanism'))
    opportunity_number: Optional[str] = Field(None, validation_alias=AliasPath('opportunity_number'))
    is_active: bool = Field(False, validation_alias=AliasPath('is_active'))
    is_array_funded: bool = Field(False, validation_alias=AliasPath('arra_funded'))
    covid_response: Optional[str] = Field(None, validation_alias=AliasPath('covid_response'))
    last_updated: Optional[datetime] = Field(None, validation_alias=AliasPath('last_update_date'))

class NIHSearchResponse(NIHBaseModel):
    """Response from NIH Reporter search endpoint"""
    meta: Dict[str, Any] = Field(validation_alias=AliasPath('meta'))
    results: List[NIHProject] = Field(validation_alias=AliasPath('results')) 