from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, AliasPath

class OrcidBaseModel(BaseModel):
    """Base model for all ORCID models with shared config"""
    model_config = ConfigDict(
        populate_by_name=True,
        extra='allow'
    )
    
class OrcidName(OrcidBaseModel):
    """Raw name data from ORCID API"""
    given_names: Optional[str] = Field(None, validation_alias=AliasPath('given-names', 'value'))
    family_name: Optional[str] = Field(None, validation_alias=AliasPath('family-name', 'value'))
    credit_name: Optional[str] = Field(None, validation_alias=AliasPath('credit-name', 'value'))

class OrcidExternalId(OrcidBaseModel):
    """Raw external identifier from ORCID API"""
    name: str = Field(validation_alias=AliasPath('external-id-type'))
    value: Optional[str] = Field(None, validation_alias=AliasPath('external-id-value', 'value'))
    url: Optional[str] = Field(None, validation_alias=AliasPath('external-id-url', 'value'))
    source: Optional[str] = Field(
        None,
        validation_alias=AliasPath('source', 'source-name', 'value')
    )
    
class OrcidExternalIdWorks(OrcidBaseModel):
    """Raw external identifier from ORCID API"""
    name: str = Field(validation_alias=AliasPath('external-id-type'))
    value: Optional[str] = Field(None, validation_alias=AliasPath('external-id-value'))
    url: Optional[str] = Field(None, validation_alias=AliasPath('external-id-url', 'value'))
    source: Optional[str] = Field(
        None,
        validation_alias=AliasPath('source', 'source-name', 'value')
    )

class OrcidUrl(OrcidBaseModel):
    """Raw researcher URL from ORCID API"""
    name: Optional[str] = Field(None, validation_alias=AliasPath('url-name'))
    url: str = Field(validation_alias=AliasPath('url', 'value'))

class OrcidEmail(OrcidBaseModel):
    """Raw email data from ORCID API"""
    email: str
    verified: bool = False
    primary: bool = False

class OrcidOrganizationAddress(OrcidBaseModel):
    """Raw organization address from ORCID API"""
    city: Optional[str] = Field(None, validation_alias=AliasPath('city', 'value'))
    region: Optional[str] = Field(None, validation_alias=AliasPath('region', 'value'))
    country: Optional[str] = Field(None, validation_alias=AliasPath('country', 'value'))
    
    
class OrcidOrganization(OrcidBaseModel):
    """Organization data from ORCID API"""
    name: str = Field(validation_alias=AliasPath('name'))
    address: Optional[OrcidOrganizationAddress] = Field(None, validation_alias=AliasPath('address'))
    disambiguation_source: Optional[str] = Field(
        None,
        validation_alias=AliasPath('disambiguated-organization', 'disambiguation-source')
    )

class OrcidAffiliation(OrcidBaseModel):
    """Education or employment affiliation"""
    organization: OrcidOrganization = Field(validation_alias=AliasPath('organization'))
    department_name: Optional[str] = Field(None, validation_alias=AliasPath('department-name'))
    role_title: Optional[str] = Field(None, validation_alias=AliasPath('role-title'))
    start_date: Optional[Dict[str, Any]] = Field(None, validation_alias=AliasPath('start-date'))
    end_date: Optional[Dict[str, Any]] = Field(None, validation_alias=AliasPath('end-date'))
    source_name: Optional[str] = Field(
        None,
        validation_alias=AliasPath('source', 'source-name', 'value')
    )

class OrcidKeyword(OrcidBaseModel):
    """Keyword from ORCID API"""
    content: str
    source: Optional[str] = Field(
        None,
        validation_alias=AliasPath('source', 'source-name', 'value')
    )

class OrcidOtherName(OrcidBaseModel):
    """Other name from ORCID API"""
    content: str
    source: Optional[str] = Field(
        None,
        validation_alias=AliasPath('source', 'source-name', 'value')
    )

class OrcidProfile(OrcidBaseModel):
    """Raw person data from ORCID API"""
    name: OrcidName = Field(validation_alias=AliasPath('name'))
    biography: Optional[str] = Field(None, validation_alias=AliasPath('biography', 'content'))
    keywords: List[OrcidKeyword] = Field(default_factory=list, validation_alias=AliasPath('keywords', 'keyword'))
    other_names: List[OrcidOtherName] = Field(default_factory=list, validation_alias=AliasPath('other-names', 'other-name'))
    emails: List[OrcidEmail] = Field(default_factory=list, validation_alias=AliasPath('emails', 'email'))
    external_ids: List[OrcidExternalId] = Field(
        default_factory=list,
        validation_alias=AliasPath('external-identifiers', 'external-identifier')
    )
    researcher_urls: List[OrcidUrl] = Field(
        default_factory=list,
        validation_alias=AliasPath('researcher-urls', 'researcher-url')
    )
    last_modified: Optional[datetime] = Field(
        None,
        validation_alias=AliasPath('last-modified-date', 'value')
    )

class OrcidWorkSummary(OrcidBaseModel):
    """Summary of a work from ORCID API"""
    title: Optional[str] = Field(None, validation_alias=AliasPath('title', 'title', 'value'))
    type: Optional[str] = Field(None, validation_alias=AliasPath('type'))
    publication_date: Optional[Dict[str, Any]] = Field(None, validation_alias=AliasPath('publication-date'))
    journal_title: Optional[str] = Field(None, validation_alias=AliasPath('journal-title', 'value'))
    url: Optional[str] = Field(None, validation_alias=AliasPath('url', 'value'))
    source: Optional[str] = Field(None, validation_alias=AliasPath('source', 'source-name', 'value'))

class OrcidWork(OrcidBaseModel):
    """Raw work data from ORCID API"""
    work_summaries: List[OrcidWorkSummary] = Field(
        default_factory=list,
        validation_alias=AliasPath('work-summary')
    )
    external_ids: List[OrcidExternalIdWorks] = Field(
        default_factory=list,
        validation_alias=AliasPath('external-ids', 'external-id')
    )

class OrcidWorks(OrcidBaseModel):
    """Container for work data"""
    works: List[OrcidWork] = Field(
        default_factory=list,
        validation_alias=AliasPath('group')
    ) 