from typing import Optional, List, Dict, Any, Union
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
    duns: Optional[List[str]] = Field(None, validation_alias=AliasPath('org_duns'))
    ueis: Optional[List[str]] = Field(None, validation_alias=AliasPath('org_ueis'))
    primary_duns: Optional[str] = Field(None, validation_alias=AliasPath('primary_duns'))
    primary_uei: Optional[str] = Field(None, validation_alias=AliasPath('primary_uei'))
    zip: Optional[str] = Field(None, validation_alias=AliasPath('org_zipcode'))
    type: Optional[str] = Field(None, validation_alias=AliasPath('org_type'))
    fips: Optional[str] = Field(None, validation_alias=AliasPath('org_fips'))
    ipf: Optional[str] = Field(None, validation_alias=AliasPath('org_ipf_code'))
    external_org_id: Optional[int] = Field(None, validation_alias=AliasPath('external_org_id'))

class NIHPrincipalInvestigator(NIHBaseModel):
    """Principal Investigator data from NIH Reporter API"""
    profile_id: Optional[int] = Field(None, validation_alias=AliasPath('profile_id'))
    first_name: Optional[str] = Field(None, validation_alias=AliasPath('first_name'))
    middle_name: Optional[str] = Field(None, validation_alias=AliasPath('middle_name'))
    last_name: Optional[str] = Field(None, validation_alias=AliasPath('last_name'))
    full_name: Optional[str] = Field(None, validation_alias=AliasPath('full_name'))
    is_contact_pi: Optional[bool] = Field(None, validation_alias=AliasPath('is_contact_pi'))
    title: Optional[str] = Field(None, validation_alias=AliasPath('title'))

class NIHProgramOfficer(NIHBaseModel):
    """Program Officer data from NIH Reporter API"""
    first_name: Optional[str] = Field(None, validation_alias=AliasPath('first_name'))
    middle_name: Optional[str] = Field(None, validation_alias=AliasPath('middle_name'))
    last_name: Optional[str] = Field(None, validation_alias=AliasPath('last_name'))
    full_name: Optional[str] = Field(None, validation_alias=AliasPath('full_name'))

class NIHStudySection(NIHBaseModel):
    """Study Section data from NIH Reporter API"""
    code: Optional[str] = Field(None, validation_alias=AliasPath('srg_code'))
    name: Optional[str] = Field(None, validation_alias=AliasPath('name'))
    flex_code: Optional[str] = Field(None, validation_alias=AliasPath('sra_flex_code'))
    designator_code: Optional[str] = Field(None, validation_alias=AliasPath('sra_designator_code'))
    group_code: Optional[str] = Field(None, validation_alias=AliasPath('group_code'))

class NIHProjectTerm(NIHBaseModel):
    """Project term/keyword from NIH Reporter API"""
    term: str = Field(validation_alias=AliasPath('term'))
    category: Optional[str] = Field(None, validation_alias=AliasPath('category'))

class NIHProjectNumSplit(NIHBaseModel):
    """Project number split into components"""
    appl_type_code: Optional[str] = Field(None, validation_alias=AliasPath('appl_type_code'))
    activity_code: Optional[str] = Field(None, validation_alias=AliasPath('activity_code'))
    ic_code: Optional[str] = Field(None, validation_alias=AliasPath('ic_code'))
    serial_num: Optional[str] = Field(None, validation_alias=AliasPath('serial_num'))
    support_year: Optional[str] = Field(None, validation_alias=AliasPath('support_year'))
    full_support_year: Optional[str] = Field(None, validation_alias=AliasPath('full_support_year'))
    suffix_code: Optional[str] = Field(None, validation_alias=AliasPath('suffix_code'))

class NIHAgencyICAdmin(NIHBaseModel):
    """NIH Agency IC Admin data"""
    code: Optional[str] = Field(None, validation_alias=AliasPath('code'))
    abbreviation: Optional[str] = Field(None, validation_alias=AliasPath('abbreviation'))
    name: Optional[str] = Field(None, validation_alias=AliasPath('name'))

class NIHAgencyICFunding(NIHBaseModel):
    """NIH Agency IC Funding data"""
    fy: Optional[int] = Field(None, validation_alias=AliasPath('fy'))
    code: Optional[str] = Field(None, validation_alias=AliasPath('code'))
    name: Optional[str] = Field(None, validation_alias=AliasPath('name'))
    abbreviation: Optional[str] = Field(None, validation_alias=AliasPath('abbreviation'))
    total_cost: Optional[float] = Field(None, validation_alias=AliasPath('total_cost'))
    direct_cost_ic: Optional[float] = Field(None, validation_alias=AliasPath('direct_cost_ic'))
    indirect_cost_ic: Optional[float] = Field(None, validation_alias=AliasPath('indirect_cost_ic'))

class NIHOrganizationType(NIHBaseModel):
    """NIH Organization Type data"""
    name: Optional[str] = Field(None, validation_alias=AliasPath('name'))
    code: Optional[str] = Field(None, validation_alias=AliasPath('code'))
    is_other: Optional[bool] = Field(None, validation_alias=AliasPath('is_other'))

class NIHGeoLatLon(NIHBaseModel):
    """Geographic latitude and longitude data"""
    lat: Optional[float] = Field(None, validation_alias=AliasPath('lat'))
    lon: Optional[float] = Field(None, validation_alias=AliasPath('lon'))

class NIHProject(NIHBaseModel):
    """Raw project data from NIH Reporter API"""
    appl_id: Optional[int] = Field(None, validation_alias=AliasPath('appl_id'))
    subproject_id: Optional[str] = Field(None, validation_alias=AliasPath('subproject_id'))
    project_num: str = Field(validation_alias=AliasPath('project_num'))
    project_serial_num: Optional[str] = Field(None, validation_alias=AliasPath('project_serial_num'))
    title: Optional[str] = Field(None, validation_alias=AliasPath('project_title'))
    abstract: Optional[str] = Field(None, validation_alias=AliasPath('abstract_text'))
    fiscal_year: Optional[int] = Field(None, validation_alias=AliasPath('fiscal_year'))
    award_amount: Optional[float] = Field(None, validation_alias=AliasPath('award_amount'))
    direct_costs: Optional[float] = Field(None, validation_alias=AliasPath('direct_cost_amt'))
    indirect_costs: Optional[float] = Field(None, validation_alias=AliasPath('indirect_cost_amt'))
    start_date: Optional[datetime] = Field(None, validation_alias=AliasPath('project_start_date'))
    end_date: Optional[datetime] = Field(None, validation_alias=AliasPath('project_end_date'))
    budget_start: Optional[datetime] = Field(None, validation_alias=AliasPath('budget_start'))
    budget_end: Optional[datetime] = Field(None, validation_alias=AliasPath('budget_end'))
    organization: Optional[NIHOrganization] = Field(None, validation_alias=AliasPath('organization'))
    principal_investigators: List[NIHPrincipalInvestigator] = Field(default_factory=list, validation_alias=AliasPath('principal_investigators'))
    contact_pi_name: Optional[str] = Field(None, validation_alias=AliasPath('contact_pi_name'))
    program_officers: List[NIHProgramOfficer] = Field(default_factory=list, validation_alias=AliasPath('program_officers'))
    study_section: Optional[NIHStudySection] = Field(None, validation_alias=AliasPath('full_study_section'))
    project_num_split: Optional[NIHProjectNumSplit] = Field(None, validation_alias=AliasPath('project_num_split'))
    agency_ic_admin: Optional[NIHAgencyICAdmin] = Field(None, validation_alias=AliasPath('agency_ic_admin'))
    agency_ic_fundings: List[NIHAgencyICFunding] = Field(default_factory=list, validation_alias=AliasPath('agency_ic_fundings'))
    organization_type: Optional[NIHOrganizationType] = Field(None, validation_alias=AliasPath('organization_type'))
    geo_lat_lon: Optional[NIHGeoLatLon] = Field(None, validation_alias=AliasPath('geo_lat_lon'))
    terms: Optional[str] = Field(None, validation_alias=AliasPath('terms'))
    pref_terms: Optional[str] = Field(None, validation_alias=AliasPath('pref_terms'))
    spending_categories: Optional[List[int]] = Field(None, validation_alias=AliasPath('spending_categories'))
    spending_categories_desc: Optional[str] = Field(None, validation_alias=AliasPath('spending_categories_desc'))
    award_type: Optional[str] = Field(None, validation_alias=AliasPath('award_type'))
    activity_code: Optional[str] = Field(None, validation_alias=AliasPath('activity_code'))
    funding_mechanism: Optional[str] = Field(None, validation_alias=AliasPath('funding_mechanism'))
    opportunity_number: Optional[str] = Field(None, validation_alias=AliasPath('opportunity_number'))
    is_active: bool = Field(False, validation_alias=AliasPath('is_active'))
    is_array_funded: bool = Field(False, validation_alias=AliasPath('arra_funded'))
    covid_response: Optional[str] = Field(None, validation_alias=AliasPath('covid_response'))
    phr_text: Optional[str] = Field(None, validation_alias=AliasPath('phr_text'))
    cong_dist: Optional[str] = Field(None, validation_alias=AliasPath('cong_dist'))
    award_notice_date: Optional[datetime] = Field(None, validation_alias=AliasPath('award_notice_date'))
    is_new: Optional[bool] = Field(None, validation_alias=AliasPath('is_new'))
    core_project_num: Optional[str] = Field(None, validation_alias=AliasPath('core_project_num'))
    cfda_code: Optional[str] = Field(None, validation_alias=AliasPath('cfda_code'))
    agency_code: Optional[str] = Field(None, validation_alias=AliasPath('agency_code'))
    date_added: Optional[datetime] = Field(None, validation_alias=AliasPath('date_added'))
    project_detail_url: Optional[str] = Field(None, validation_alias=AliasPath('project_detail_url'))

class NIHSearchResponse(NIHBaseModel):
    """Response from NIH Reporter search endpoint"""
    meta: Dict[str, Any] = Field(validation_alias=AliasPath('meta'))
    results: List[NIHProject] = Field(validation_alias=AliasPath('results')) 