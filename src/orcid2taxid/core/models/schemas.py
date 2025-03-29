from typing import List, Dict, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from collections import defaultdict
import json

class CustomBaseModel(BaseModel):
    """Base model with custom JSON serialization configuration"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    )

class AuthorAffiliation(CustomBaseModel):
    """Represents an author's affiliation with an institution"""
    institution_name: str
    department: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ExternalId(CustomBaseModel):
    """Represents an external identifier with its value, URL and metadata"""
    value: str
    url: Optional[str] = None
    relationship: Optional[str] = None

class ResearcherUrl(CustomBaseModel):
    """Represents a researcher's URL (e.g. personal website, LinkedIn)"""
    name: Optional[str] = None
    url: str

class EmailInfo(CustomBaseModel):
    """Represents an email address with its metadata"""
    address: str
    verified: bool = False
    primary: bool = False

class CountryInfo(CustomBaseModel):
    """Represents a country with its metadata"""
    code: str


class Author(CustomBaseModel):
    """Simplified author information as it appears in a publication"""
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    full_name: str
    orcid: Optional[str] = None
    email: Optional[str] = None
    affiliations: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    sequence: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)

class FundingInfo(CustomBaseModel):
    """Represents funding information for a publication"""
    name: Optional[str] = None
    funder: Optional[str] = None
    grant_number: Optional[str] = None

class GrantMetadata(CustomBaseModel):
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

class NCBITaxonomyInfo(CustomBaseModel):
    """Represents comprehensive taxonomy information from NCBI"""
    taxid: int = Field(description="NCBI Taxonomy ID")
    scientific_name: str = Field(description="Scientific name of the organism")
    rank: Optional[str] = Field(description="Taxonomic rank (e.g., species, genus)")
    division: Optional[str] = Field(description="Division/domain (e.g., Bacteria, Viruses)")
    common_name: Optional[str] = Field(description="Common name if available")
    lineage: Optional[List[str]] = Field(description="Full taxonomic lineage")
    synonyms: Optional[List[str]] = Field(description="List of synonyms")
    genetic_code: Optional[str] = Field(description="Genetic code used by the organism")
    mito_genetic_code: Optional[str] = Field(description="Mitochondrial genetic code if applicable")
    is_parasite: Optional[bool] = Field(description="Whether the organism is parasitic")
    is_pathogen: Optional[bool] = Field(description="Whether the organism is pathogenic")
    host_taxid: Optional[int] = Field(description="TaxID of the primary host if parasitic/pathogenic")
    host_scientific_name: Optional[str] = Field(description="Scientific name of the primary host")

class OrganismMention(CustomBaseModel):
    """Represents a mention of an organism in text"""
    original_name: str = Field(description="Original organism name as found in text")
    searchable_name: str = Field(description="Searchable organism name for NCBI database")
    context: Optional[str] = Field(description="Context in which the organism was mentioned")
    confidence: Optional[float] = Field(description="Confidence score of the extraction")
    justification: Optional[str] = Field(description="Explanation of why this organism was included")
    taxonomy_info: Optional[NCBITaxonomyInfo] = Field(default=None, description="NCBI taxonomy information for the organism")


from typing import Optional, List, Literal
from pydantic import BaseModel, Field

# Define Literal types for each category
WetLabStatus = Literal["yes", "no", "mixed", "undetermined"]

BSLLevel = Literal[
    "bsl_1",     # Well-characterized agents not known to cause disease in healthy adults
    "bsl_2",     # Agents of moderate potential hazard to personnel and environment
    "bsl_3",     # Indigenous or exotic agents with potential for aerosol transmission
    "bsl_4",     # Dangerous/exotic agents with high risk of life-threatening disease
    "not_specified",  # BSL level not mentioned in publication
    "not_applicable"  # BSL classification not relevant to this work
]

DNAUseType = Literal[
    "gene_expression",      # Production of RNA/protein from synthetic DNA
    "cloning",              # Construction of recombinant DNA molecules
    "genome_editing",       # Modification of genomic DNA (CRISPR, etc.)
    "library_construction", # Creation of collections of DNA molecules
    "diagnostics",          # Development/use of diagnostic tests or assays
    "vaccine_development",  # Creation of vaccine candidates
    "therapeutics",         # Development of therapeutic agents
    "primers_probes",       # Use as primers or probes for PCR/hybridization
    "structure_studies",    # Investigation of DNA/RNA structure
    "metabolic_engineering", # Alteration of cellular metabolism
    "synthetic_biology",    # Engineering novel biological parts/systems
    "other_specified",      # Other use clearly specified in publication
    "not_specified"         # Use not clearly specified in publication
]

NovelSequenceUse = Literal[
    "yes", # Multiple previous publications with novel/hybrid sequences
    "no",   # One or few previous publications with novel/hybrid sequences
    "unclear"    # Cannot be determined from available publications
]

DNAType = Literal[
    "oligonucleotides",    # Short DNA sequences, typically <100bp
    "gene_fragments",      # Partial genes or genetic elements
    "complete_genes",      # Full-length genes
    "regulatory_elements", # Promoters, enhancers, etc.
    "vectors",             # Plasmids, viral vectors, etc.
    "whole_genome",        # Complete genomes or chromosomes
    "multiple_types",      # Combination of different DNA types
    "synthetic_genome",    # Fully or partially synthetic genome
    "other_specified",     # Other type clearly specified in publication
    "not_specified"        # Type not clearly specified in publication
]

class PaperClassificationMetadata(BaseModel):
    wet_lab_work: WetLabStatus = Field(
        ..., 
        description="Whether the publication involves wet lab work"
    )
    
    bsl_level: BSLLevel = Field(
        ..., 
        description="Highest Biosafety Level mentioned in the work"
    )
    
    dna_use: List[DNAUseType] = Field(
        ..., 
        description="How the synthetic DNA is being used"
    )
    
    novel_sequence_experience: NovelSequenceUse = Field(
        ..., 
        description="Researcher's experience with novel/hybrid sequences"
    )
    
    dna_type: List[DNAType] = Field(
        ..., 
        description="Type of synthetic DNA used in the research"
    )
    
    additional_notes: Optional[str] = Field(
        None, 
        description="Additional relevant information about the publication"
    )

class PaperMetadata(CustomBaseModel):
    """Represents metadata for a scientific publication"""
    title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[datetime] = None
    journal_name: Optional[str] = None
    journal_issn: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    full_text_url: Optional[str] = None
    citation_count: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    funding_info: List[GrantMetadata] = Field(default_factory=list)
    organisms: List[OrganismMention] = Field(default_factory=list)
    classification: Optional[PaperClassificationMetadata] = None

class ResearcherMetadata(CustomBaseModel):
    """Represents metadata for a researcher"""
    orcid: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[EmailInfo] = None
    
    # Core fields that are always populated from ORCID
    full_name: str
    credit_name: Optional[str] = None
    biography: Optional[str] = None
    researcher_urls: List[ResearcherUrl] = Field(default_factory=list)
    country: Optional[CountryInfo] = None
    last_modified: Optional[datetime] = None
    
    # Fields that can be enriched from publications
    alternative_names: Set[str] = Field(default_factory=set)
    keywords: Set[str] = Field(default_factory=set)
    subjects: Set[str] = Field(default_factory=set)
    journals: Set[str] = Field(default_factory=set)
    external_ids: Dict[str, ExternalId] = Field(default_factory=dict)
    education: List[AuthorAffiliation] = Field(default_factory=list)
    affiliations: List[AuthorAffiliation] = Field(default_factory=list)
    
    # Publications
    publications: List[PaperMetadata] = Field(default_factory=list)
    
    # Grants
    grants: List[GrantMetadata] = Field(default_factory=list)
    
    def get_publication_count(self) -> int:
        """Get total number of publications"""
        return len(self.publications)
    
    def get_publications_sorted_by_date(self) -> List[PaperMetadata]:
        """Get publications sorted by date in descending order (newest first)"""
        return sorted(
            [p for p in self.publications if p.publication_date],
            key=lambda x: x.publication_date,
            reverse=True
        )
    
    def get_publications_by_journal(self) -> Dict[str, List[PaperMetadata]]:
        """Get publications grouped by journal"""
        by_journal = defaultdict(list)
        for paper in self.publications:
            if paper.journal_name:
                by_journal[paper.journal_name].append(paper)
        return dict(by_journal)
    
    def get_publications_by_organism(self) -> Dict[str, List[PaperMetadata]]:
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

    def get_grants_by_funder(self) -> Dict[str, List[GrantMetadata]]:
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

    def get_affiliations_by_institution(self) -> Dict[str, List[AuthorAffiliation]]:
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

    def format_affiliation_time_range(self, affiliation: AuthorAffiliation) -> str:
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

    def format_affiliation_role(self, affiliation: AuthorAffiliation) -> str:
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

    def format_education_time_range(self, education: AuthorAffiliation) -> str:
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
