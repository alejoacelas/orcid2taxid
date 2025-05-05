from pydantic import BaseModel, Field, ConfigDict, AliasPath, field_validator
from typing import Optional, List, Dict, Any

class NCBIBaseModel(BaseModel):
    """Base model for all NCBI models with shared config"""
    model_config = ConfigDict(
        populate_by_name=True,
        extra='allow'  # Allow extra fields as the API response is complex
    )

class NCBITaxonomyInfo(NCBIBaseModel):
    """Represents comprehensive taxonomy information from NCBI"""
    taxid: int = Field(description="NCBI Taxonomy ID")
    scientific_name: str = Field(description="Scientific name of the organism")
    rank: Optional[str] = Field(None, description="Taxonomic rank (e.g., species, genus)")
    division: Optional[str] = Field(None, description="Division/domain (e.g., Bacteria, Viruses)")
    common_name: Optional[str] = Field(None, description="Common name if available")
    lineage: Optional[List[str]] = Field(None, description="Full taxonomic lineage")
    synonyms: Optional[List[str]] = Field(None, description="List of synonyms")
    genetic_code: Optional[str] = Field(None, description="Genetic code used by the organism")
    mito_genetic_code: Optional[str] = Field(None, description="Mitochondrial genetic code if applicable")
    is_parasite: Optional[bool] = Field(None, description="Whether the organism is parasitic")
    is_pathogen: Optional[bool] = Field(None, description="Whether the organism is pathogenic")
    host_taxid: Optional[int] = Field(None, description="TaxID of the primary host if parasitic/pathogenic")
    host_scientific_name: Optional[str] = Field(None, description="Scientific name of the primary host")

    @field_validator('lineage', mode='before')
    @classmethod
    def parse_lineage(cls, v: Optional[str]) -> Optional[List[str]]:
        """Convert lineage string to list if it's a string"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(';')]
        return v

    @field_validator('host_taxid', mode='before')
    @classmethod
    def parse_host_taxid(cls, v: Optional[str]) -> Optional[int]:
        """Convert host_taxid to int if it's a string"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

class NCBISearchResult(NCBIBaseModel):
    """Represents the search result from NCBI esearch endpoint"""
    count: int = Field(description="Number of results found")
    ret_max: int = Field(description="Maximum number of results returned", validation_alias=AliasPath('retmax'))
    ret_start: int = Field(description="Starting position of results", validation_alias=AliasPath('retstart'))
    id_list: List[str] = Field(description="List of taxonomy IDs found", validation_alias=AliasPath('idlist'))

class NCBITaxRecord(NCBIBaseModel):
    """Represents a taxonomy record from NCBI esummary endpoint"""
    uid: str = Field(description="Taxonomy ID")
    scientific_name: str = Field(description="Scientific name", validation_alias=AliasPath('scientificname'))
    rank: Optional[str] = Field(None, description="Taxonomic rank")
    division: Optional[str] = Field(None, description="Taxonomic division")
    common_name: Optional[str] = Field(None, description="Common name", validation_alias=AliasPath('commonname'))
    lineage: Optional[str] = Field(None, description="Lineage as a string")
    synonym: Optional[List[str]] = Field(None, description="Synonyms")
    genetic_code: Optional[str] = Field(None, description="Genetic code", validation_alias=AliasPath('gencode'))
    mito_genetic_code: Optional[str] = Field(None, description="Mitochondrial genetic code", validation_alias=AliasPath('mitogenome'))
    is_parasite: Optional[bool] = Field(None, description="Is parasite", validation_alias=AliasPath('parasite'))
    is_pathogen: Optional[bool] = Field(None, description="Is pathogen", validation_alias=AliasPath('pathogen'))
    host_taxid: Optional[str] = Field(None, description="Host taxonomy ID")
    host_scientific_name: Optional[str] = Field(None, description="Host scientific name", validation_alias=AliasPath('host_scientificname'))

class NCBITaxonomyResponse(NCBIBaseModel):
    """Represents the full response from NCBI esummary endpoint"""
    uids: List[str] = Field(description="List of taxonomy IDs")
    result: Dict[str, NCBITaxRecord] = Field(description="Taxonomy records indexed by ID") 