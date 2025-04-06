from pydantic import BaseModel, Field
from typing import Optional, List

class NCBITaxonomyInfo(BaseModel):
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

class OrganismMention(BaseModel):
    """Represents a mention of an organism in text"""
    original_name: str = Field(description="Original organism name as found in text")
    searchable_name: str = Field(description="Searchable organism name for NCBI database")
    context: Optional[str] = Field(description="Context in which the organism was mentioned")
    confidence: Optional[float] = Field(description="Confidence score of the extraction")
    justification: Optional[str] = Field(description="Explanation of why this organism was included")
    taxonomy_info: Optional[NCBITaxonomyInfo] = Field(default=None, description="NCBI taxonomy information for the organism")
