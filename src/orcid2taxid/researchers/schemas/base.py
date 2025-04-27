from typing import List, Dict
from collections import defaultdict
from datetime import datetime
from pydantic import Field
from orcid2taxid.shared.schemas import (
    ResearcherID, ExternalReference, InstitutionalAffiliation,
    ResearcherDescription, ResearcherProfile, EmailInfo
)
from orcid2taxid.grants.schemas import GrantRecord
from orcid2taxid.publications.schemas.base import PublicationRecord
from orcid2taxid.researchers.schemas.orcid import OrcidProfile, OrcidAffiliation, OrcidWorks
from orcid2taxid.core.utils.date import parse_date

class CustomerProfile(ResearcherProfile):
    """Core customer profile information"""    
    publications: List[PublicationRecord] = Field(default_factory=list)
    grants: List[GrantRecord] = Field(default_factory=list)
    
    @classmethod
    def from_orcid_profile(cls, orcid_profile: OrcidProfile, orcid_id: str) -> "CustomerProfile":
        """Create a customer profile from an ORCID profile"""
        emails = sorted(orcid_profile.emails, key=lambda x: (x.primary, x.verified), reverse=True)
        researcher_id = ResearcherID(
            orcid=orcid_id,
            given_name=orcid_profile.name.given_names,
            family_name=orcid_profile.name.family_name,
            credit_name=orcid_profile.name.credit_name,
            emails=[EmailInfo(address=email.email, primary=email.primary) for email in emails]
        )
        
        description = ResearcherDescription()
        if orcid_profile.biography:
            description.add_section("ORCID Profile Biography", orcid_profile.biography)
        if orcid_profile.keywords:
            description.add_section("ORCID Profile Keywords", ", ".join(orcid_profile.keywords))
        
        external_references = []
        for ext_id in orcid_profile.external_ids:
            external_references.append(ExternalReference(url=ext_id.url, name=ext_id.name, source=ext_id.source))
        for url in orcid_profile.researcher_urls:
            external_references.append(ExternalReference(url=url.url, name=url.name, source="ORCID Profile"))
            
        return cls(
            researcher_id=researcher_id,
            description=description,
            external_references=external_references
        )
            
    def add_educations_from_orcid(self, educations: List[OrcidAffiliation]) -> 'CustomerProfile':
        """Add educations from ORCID affiliations"""
        for education in educations:
            self.educations.append(InstitutionalAffiliation(  # pylint: disable=no-member
                institution=education.organization.name,
                department=education.department_name,
                role=education.role_title,
                start_date=parse_date(education.start_date),
                end_date=parse_date(education.end_date)
            ))
        return self
    
    def add_employments_from_orcid(self, employments: List[OrcidAffiliation]) -> 'CustomerProfile':
        """Add employments from ORCID affiliations"""
        for employment in employments:
            self.employments.append(InstitutionalAffiliation(  # pylint: disable=no-member
                institution=employment.organization.name,
                department=employment.department_name,
                role=employment.role_title,
                start_date=parse_date(employment.start_date),
                end_date=parse_date(employment.end_date)
            ))
        return self
    
    def add_publications_from_orcid(self, works: List[OrcidWorks]) -> 'CustomerProfile':
        """Add publications from ORCID works"""
        for work in works.works:
            summaries = work.work_summaries
            
            title = next((summary.title for summary in summaries if summary.title), None)
            pub_date = next((summary.publication_date for summary in summaries if summary.publication_date), None)
            journal = next((summary.journal_title for summary in summaries if summary.journal_title), None)
            
            # types = [summary.type for summary in summaries if summary.type]
            sources = [summary.source for summary in summaries if summary.source]
        
            # Find DOI from external IDs
            print(work.external_ids)
            doi = next((ext_id.value for ext_id in work.external_ids if ext_id.name == 'doi'), None)
                
            # Create publication record
            if not title:
                continue
            
            pub_record = PublicationRecord(
                title=title,
                publication_date=parse_date(pub_date),
                journal_name=journal,
                source=", ".join(sources) if sources else None,
                doi=doi
            )
            
            self.publications.append(pub_record)  # pylint: disable=no-member
        return self
    
    def get_publication_count(self) -> int:
        """Get total number of publications"""
        return len(self.publications)
    
    def get_publications_sorted_by_date(self) -> List[PublicationRecord]:
        """Get publications sorted by date in descending order (newest first)"""
        return sorted(
            [p for p in self.publications if p.publication_date],
            key=lambda x: x.publication_date,
            reverse=True
        )
    
    def get_publications_by_journal(self) -> Dict[str, List[PublicationRecord]]:
        """Get publications grouped by journal"""
        by_journal = defaultdict(list)
        for paper in self.publications:
            if paper.journal_name:
                by_journal[paper.journal_name].append(paper)
        return dict(by_journal)
    
    def get_publications_by_organism(self) -> Dict[str, List[PublicationRecord]]:
        """Get publications grouped by organism"""
        by_organism = defaultdict(list)
        for paper in self.publications:
            # Skip if organisms is not a list (e.g., if it's a RuntimeError)
            if not isinstance(paper.organisms, list):
                continue
                
            if paper.organisms:  # Check if organisms list exists and is not empty
                for organism in paper.organisms:
                    if organism.taxonomy_info and organism.taxonomy_info.scientific_name:
                        by_organism[organism.taxonomy_info.scientific_name].append(paper)
        return dict(by_organism)

    def get_grants_by_funder(self) -> Dict[str, List[GrantRecord]]:
        """Get grants grouped by funder, with special handling for single-grant funders.
        
        Returns:
            Dict[str, List[GrantMetadata]]: Dictionary mapping funder names to their grants.
            Single-grant funders are grouped under 'Other Funders' unless all funders have
            only one grant, in which case they are grouped under 'Multiple Funders'.
            Funders are sorted by number of grants in descending order.
        """
        # First, group grants by funder
        by_funder = defaultdict(list)
        for grant in self.grants:
            funder = grant.funder or "Unknown Funder"
            by_funder[funder].append(grant)
        
        # Sort grants within each funder group by completeness
        for funder in by_funder:
            by_funder[funder] = sorted(
                by_funder[funder],
                key=lambda g: (
                    bool(g.project_title and g.abstract_text),
                    bool(g.project_title),
                    bool(g.abstract_text)
                ),
                reverse=True
            )
        
        # Handle single-grant funders
        result = {}
        single_grant_funders = []
        
        # Sort funders by number of grants
        sorted_funders = sorted(by_funder.items(), key=lambda x: len(x[1]), reverse=True)
        
        for funder, grants in sorted_funders:
            if len(grants) == 1:
                single_grant_funders.append((funder, grants[0]))
            else:
                result[funder] = grants
        
        # If we have single-grant funders, check if all funders have only one grant
        if single_grant_funders:
            if len(single_grant_funders) == len(by_funder):
                # All funders have only one grant
                result["Multiple Funders"] = [grant for _, grant in single_grant_funders]
            else:
                # Some funders have multiple grants, group single-grant funders under "Other Funders"
                result["Other Funders"] = [grant for _, grant in single_grant_funders]
        
        return result

    def get_affiliations_by_institution(self) -> Dict[str, List[InstitutionalAffiliation]]:
        """Get affiliations grouped by institution name, with roles sorted by date.
        
        Returns:
            Dict[str, List[AuthorAffiliation]]: Dictionary mapping institution names to their affiliations,
            sorted by start date in descending order (most recent first).
        """
        # Group affiliations by institution
        by_institution = defaultdict(list)
        for affiliation in self.affiliations:
            by_institution[affiliation.institution_name].append(affiliation)
        
        # Sort affiliations within each institution by start date
        for institution in by_institution:
            by_institution[institution] = sorted(
                by_institution[institution],
                key=lambda x: (x.start_date or datetime.min, x.end_date or datetime.max),
                reverse=True
            )
        
        return dict(by_institution)

    def format_affiliation_time_range(self, affiliation: InstitutionalAffiliation) -> str:
        """Format the time range for an affiliation.
        
        Args:
            affiliation: The affiliation to format
            
        Returns:
            str: Formatted time range string
        """
        if not affiliation.start_date:
            return ""
            
        start_year = affiliation.start_date.strftime('%Y')
        if not affiliation.end_date:
            return f"({start_year} - Present)"
        else:
            end_year = affiliation.end_date.strftime('%Y')
            return f"({start_year} - {end_year})"

    def format_affiliation_role(self, affiliation: InstitutionalAffiliation) -> str:
        """Format the role and department for an affiliation.
        
        Args:
            affiliation: The affiliation to format
            
        Returns:
            str: Formatted role string
        """
        parts = []
        if affiliation.role:
            parts.append(affiliation.role)
        if affiliation.department:
            parts.append(affiliation.department)
        return ", ".join(parts) if parts else ""

    def format_education_time_range(self, education: InstitutionalAffiliation) -> str:
        """Format the time range for an education entry.
        
        Args:
            education: The education entry to format
            
        Returns:
            str: Formatted time range string
        """
        if not education.start_date:
            return ""
            
        start_year = education.start_date.strftime('%Y')
        if not education.end_date:
            return f"({start_year} - Present)"
        else:
            end_year = education.end_date.strftime('%Y')
            return f"({start_year} - {end_year})"