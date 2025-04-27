from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, AliasPath

class EpmcBaseModel(BaseModel):
    """Base model for all EPMC models with shared config"""
    model_config = ConfigDict(
        populate_by_name=True,
        extra='allow'  # Allow extra fields as the API response is complex
    )

class EpmcAuthorId(EpmcBaseModel):
    """Author identifier (e.g., ORCID)"""
    type: Optional[str] = Field(None)
    value: Optional[str] = Field(None)

class EpmcAuthorAffiliation(EpmcBaseModel):
    """Author affiliation details"""
    affiliation: Optional[str] = Field(None)

class EpmcAuthor(EpmcBaseModel):
    """Author details from EPMC response"""
    full_name: Optional[str] = Field(None, validation_alias=AliasPath('fullName'))
    first_name: Optional[str] = Field(None, validation_alias=AliasPath('firstName'))
    last_name: Optional[str] = Field(None, validation_alias=AliasPath('lastName'))
    initials: Optional[str] = Field(None)
    author_id: Optional[EpmcAuthorId] = Field(None, validation_alias=AliasPath('authorId'))
    affiliation_details: Optional[List[EpmcAuthorAffiliation]] = Field(
        default_factory=list,
        validation_alias=AliasPath('authorAffiliationDetailsList', 'authorAffiliation')
    )

class EpmcJournal(EpmcBaseModel):
    """Journal details"""
    title: Optional[str] = Field(None)
    medline_abbreviation: Optional[str] = Field(None, validation_alias=AliasPath('medlineAbbreviation'))
    nlmid: Optional[str] = Field(None)
    isoabbreviation: Optional[str] = Field(None)
    issn: Optional[str] = Field(None)
    essn: Optional[str] = Field(None)

class EpmcJournalInfo(EpmcBaseModel):
    """Journal issue and publication info"""
    issue: Optional[str] = Field(None)
    volume: Optional[str] = Field(None)
    journal_issue_id: Optional[int] = Field(None, validation_alias=AliasPath('journalIssueId'))
    date_of_publication: Optional[str] = Field(None, validation_alias=AliasPath('dateOfPublication'))
    month_of_publication: Optional[int] = Field(None, validation_alias=AliasPath('monthOfPublication'))
    year_of_publication: Optional[int] = Field(None, validation_alias=AliasPath('yearOfPublication'))
    print_publication_date: Optional[str] = Field(None, validation_alias=AliasPath('printPublicationDate'))
    journal: Optional[EpmcJournal] = Field(None)

class EpmcGrant(EpmcBaseModel):
    """Grant information"""
    grant_id: Optional[str] = Field(None, validation_alias=AliasPath('grantId'))
    agency: Optional[str] = Field(None)
    acronym: Optional[str] = Field(None)
    order_in: Optional[int] = Field(None, validation_alias=AliasPath('orderIn'))

class EpmcMeshQualifier(EpmcBaseModel):
    """MeSH qualifier details"""
    abbreviation: Optional[str] = Field(None)
    qualifier_name: Optional[str] = Field(None, validation_alias=AliasPath('qualifierName'))
    major_topic_yn: Optional[str] = Field(None, validation_alias=AliasPath('majorTopic_YN')) # Yes/No flag

class EpmcMeshHeading(EpmcBaseModel):
    """MeSH heading details"""
    major_topic_yn: Optional[str] = Field(None, validation_alias=AliasPath('majorTopic_YN')) # Yes/No flag
    descriptor_name: Optional[str] = Field(None, validation_alias=AliasPath('descriptorName'))
    mesh_qualifier_list: Optional[List[EpmcMeshQualifier]] = Field(
        default_factory=list,
        validation_alias=AliasPath('meshQualifierList', 'meshQualifier')
    )

class EpmcFullTextUrl(EpmcBaseModel):
    """Full text URL details"""
    availability: Optional[str] = Field(None)
    availability_code: Optional[str] = Field(None, validation_alias=AliasPath('availabilityCode'))
    document_style: Optional[str] = Field(None, validation_alias=AliasPath('documentStyle'))
    site: Optional[str] = Field(None)
    url: Optional[str] = Field(None)

class EpmcResult(EpmcBaseModel):
    """A single publication result from EPMC"""
    id: Optional[str] = Field(None)
    source: Optional[str] = Field(None)
    pmid: Optional[str] = Field(None)
    pmcid: Optional[str] = Field(None)
    doi: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    author_string: Optional[str] = Field(None, validation_alias=AliasPath('authorString'))
    author_list: Optional[List[EpmcAuthor]] = Field(
        default_factory=list,
        validation_alias=AliasPath('authorList', 'author')
    )
    author_id_list: Optional[List[EpmcAuthorId]] = Field(
        default_factory=list,
        validation_alias=AliasPath('authorIdList', 'authorId')
    )
    journal_info: Optional[EpmcJournalInfo] = Field(None, validation_alias=AliasPath('journalInfo'))
    pub_year: Optional[str] = Field(None, validation_alias=AliasPath('pubYear'))
    page_info: Optional[str] = Field(None, validation_alias=AliasPath('pageInfo'))
    abstract_text: Optional[str] = Field(None, validation_alias=AliasPath('abstractText'))
    affiliation: Optional[str] = Field(None) # Top-level affiliation often matches first author's first affiliation
    language: Optional[str] = Field(None)
    pub_type_list: Optional[List[str]] = Field(
        default_factory=list,
        validation_alias=AliasPath('pubTypeList', 'pubType')
    )
    keyword_list: Optional[List[str]] = Field(
        default_factory=list,
        validation_alias=AliasPath('keywordList', 'keyword')
    )
    grants_list: Optional[List[EpmcGrant]] = Field(
        default_factory=list,
        validation_alias=AliasPath('grantsList', 'grant')
    )
    mesh_heading_list: Optional[List[EpmcMeshHeading]] = Field(
        default_factory=list,
        validation_alias=AliasPath('meshHeadingList', 'meshHeading')
    )
    full_text_url_list: Optional[List[EpmcFullTextUrl]] = Field(
        default_factory=list,
        validation_alias=AliasPath('fullTextUrlList', 'fullTextUrl')
    )
    is_open_access: Optional[str] = Field(None, validation_alias=AliasPath('isOpenAccess')) # Yes/No flag
    cited_by_count: Optional[int] = Field(None, validation_alias=AliasPath('citedByCount'))
    has_references: Optional[str] = Field(None, validation_alias=AliasPath('hasReferences')) # Yes/No flag
    has_text_mined_terms: Optional[str] = Field(None, validation_alias=AliasPath('hasTextMinedTerms')) # Yes/No flag
    first_publication_date: Optional[str] = Field(None, validation_alias=AliasPath('firstPublicationDate'))

class EpmcResultList(EpmcBaseModel):
    """Container for the list of results"""
    result: List[EpmcResult] = Field(default_factory=list)

class EpmcResponse(EpmcBaseModel):
    """Top-level EPMC API response"""
    version: Optional[str] = Field(None)
    hit_count: Optional[int] = Field(None, validation_alias=AliasPath('hitCount'))
    result_list: Optional[EpmcResultList] = Field(None, validation_alias=AliasPath('resultList')) 