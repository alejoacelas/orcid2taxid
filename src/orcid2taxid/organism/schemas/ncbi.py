from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class NCBITaxonomyInfo(BaseModel):
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

class NCBISearchResult(BaseModel):
    """Represents the search result from NCBI esearch endpoint"""
    count: int = Field(description="Number of results found")
    ret_max: int = Field(description="Maximum number of results returned")
    ret_start: int = Field(description="Starting position of results")
    id_list: List[str] = Field(description="List of taxonomy IDs found")
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "NCBISearchResult":
        """Create from NCBI esearch response"""
        esearch_result = data.get("esearchresult", {})
        return cls(
            count=int(esearch_result.get("count", 0)),
            ret_max=int(esearch_result.get("retmax", 0)),
            ret_start=int(esearch_result.get("retstart", 0)),
            id_list=esearch_result.get("idlist", [])
        )

class NCBITaxRecord(BaseModel):
    """Represents a taxonomy record from NCBI esummary endpoint"""
    uid: str = Field(description="Taxonomy ID")
    scientific_name: str = Field(alias="scientificname", description="Scientific name")
    rank: Optional[str] = Field(None, description="Taxonomic rank")
    division: Optional[str] = Field(None, description="Taxonomic division")
    common_name: Optional[str] = Field(None, alias="commonname", description="Common name")
    lineage: Optional[str] = Field(None, description="Lineage as a string")
    synonym: Optional[List[str]] = Field(None, description="Synonyms")
    genetic_code: Optional[str] = Field(None, alias="gencode", description="Genetic code")
    mito_genetic_code: Optional[str] = Field(None, alias="mitogenome", description="Mitochondrial genetic code")
    is_parasite: Optional[bool] = Field(None, alias="parasite", description="Is parasite")
    is_pathogen: Optional[bool] = Field(None, alias="pathogen", description="Is pathogen")
    host_taxid: Optional[str] = Field(None, description="Host taxonomy ID")
    host_scientific_name: Optional[str] = Field(None, alias="host_scientificname", description="Host scientific name")
    
    class Config:
        populate_by_name = True

class NCBITaxonomyResponse(BaseModel):
    """Represents the full response from NCBI esummary endpoint"""
    uids: List[str] = Field(description="List of taxonomy IDs")
    result: Dict[str, NCBITaxRecord] = Field(description="Taxonomy records indexed by ID")
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "NCBITaxonomyResponse":
        """Create from NCBI esummary response"""
        result = data.get("result", {})
        uids = result.get("uids", [])
        
        # Create a new dictionary with properly validated NCBITaxRecord objects
        tax_records = {}
        for uid in uids:
            if str(uid) in result:
                try:
                    tax_records[str(uid)] = NCBITaxRecord.model_validate(result[str(uid)])
                except Exception:
                    # Skip invalid records
                    continue
        
        return cls(
            uids=uids,
            result=tax_records
        ) 