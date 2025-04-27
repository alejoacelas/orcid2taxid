from typing import Optional, List
from datetime import datetime
from pydantic import Field
from orcid2taxid.shared.schemas import (
    DatetimeSerializableBaseModel, ResearcherProfile,
    ResearcherID, ExternalReference, InstitutionalAffiliation
)
from orcid2taxid.grants.schemas import GrantRecord
from orcid2taxid.publications.schemas.epmc import EpmcResponse
from orcid2taxid.core.utils.date import parse_date
# from orcid2taxid.core.models.extraction_schemas import PaperClassificationMetadata
# from orcid2taxid.core.models.integrations.ncbi_schemas import OrganismMention


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
    grants: List[GrantRecord] = Field(default_factory=list)
    
    # organisms: List[OrganismMention] = Field(default_factory=list)
    # classification: Optional[PaperClassificationMetadata] = None

    @classmethod
    def from_epmc_response(cls, epmc_response: EpmcResponse) -> List['PublicationRecord']:
        """Convert an EpmcResponse object to a list of PublicationRecord objects.
        
        Args:
            epmc_response: The EpmcResponse object to convert
            
        Returns:
            List[PublicationRecord]: List of converted publication records
        """
        if not epmc_response.result_list or not epmc_response.result_list.result:
            return []
            
        publications = []
        for result in epmc_response.result_list.result:
            # Convert authors to ResearcherProfile objects
            authors = []
            if result.author_list:
                for author in result.author_list:
                    if not author.full_name:
                        continue
                    
                    # Handle author IDs
                    external_references = []
                    orcid = None
                    
                    # Process author IDs from author_id field
                    if author.author_id:
                        if author.author_id.type and author.author_id.value:
                            if author.author_id.type.upper() == "ORCID":
                                orcid = author.author_id.value
                            else:
                                external_references.append(ExternalReference(
                                    url=f"https://{author.author_id.type.lower()}.org/{author.author_id.value}",
                                    name=author.author_id.type,
                                    source="Europe PMC"
                                ))
                    
                    # Create researcher profile with all available information
                    researcher_id = ResearcherID(
                        given_name=author.first_name or author.initials,
                        family_name=author.last_name,
                        credit_name=author.full_name,
                        orcid=orcid
                    )
                    
                    # Handle affiliations
                    employments = []
                    if author.affiliation_details:
                        for aff_detail in author.affiliation_details:
                            if aff_detail.affiliation:
                                employments.append(InstitutionalAffiliation(
                                    institution=aff_detail.affiliation
                                ))
                                
                    researcher_profile = ResearcherProfile(
                        researcher_id=researcher_id,
                        external_references=external_references,
                        employments=employments  # Add affiliations here
                    )
                    authors.append(researcher_profile)
            
            # Convert grants to GrantRecord objects
            grants = []
            if result.grants_list:
                for grant in result.grants_list:
                    if grant.grant_id:
                        grant_record = GrantRecord(
                            id=grant.grant_id,
                            funder=grant.agency,
                        )
                        grants.append(grant_record)
            
            # Get full text URL if available
            full_text_url = None
            if result.full_text_url_list:
                for url in result.full_text_url_list:
                    if url.url:
                        full_text_url = url.url
                        break
            
            # Prepare subjects list with qualifiers
            subjects = []
            if result.mesh_heading_list:
                for mesh in result.mesh_heading_list:
                    if not mesh.descriptor_name:
                        continue # Skip if no descriptor name

                    subject_str = mesh.descriptor_name
                    
                    # Prepend '*' if it's a major topic
                    if mesh.major_topic_yn == 'Y':
                        subject_str = f"*{subject_str}"

                    # Add qualifiers if they exist
                    if mesh.mesh_qualifier_list:
                        for qualifier in mesh.mesh_qualifier_list:
                            if qualifier.qualifier_name:
                                subject_str += f"/{qualifier.qualifier_name}"
                    
                    subjects.append(subject_str)
            
            if not result.title or not result.abstract_text:
                continue

            publication = cls(
                title=result.title or "",
                abstract=result.abstract_text,
                doi=result.doi,
                publication_date=parse_date(result.first_publication_date),
                journal_name=result.journal_info.journal.title if result.journal_info and result.journal_info.journal else None,
                journal_issn=result.journal_info.journal.issn if result.journal_info and result.journal_info.journal else None,
                authors=authors,
                source="Europe PMC",
                full_text_url=full_text_url,
                citation_count=result.cited_by_count,
                keywords=result.keyword_list or [],
                subjects=subjects,
                grants=grants
            )
            publications.append(publication)
            
        return publications