from pydantic import BaseModel, Field, ConfigDict, AliasPath, model_validator
from typing import Optional, List, Dict, Union, Any

class NCBIBaseModel(BaseModel):
    """Base model for all NCBI models with shared config"""
    model_config = ConfigDict(
        populate_by_name=True,
        extra='allow'  # Allow extra fields as the API response is complex
    )

class NCBISearchResult(NCBIBaseModel):
    """Represents the search result from NCBI esearch endpoint"""
    count: Union[str, int] = Field(description="Number of results found", validation_alias=AliasPath('esearchresult', 'count'))
    ret_max: Union[str, int] = Field(description="Maximum number of results returned", validation_alias=AliasPath('esearchresult', 'retmax'))
    ret_start: Union[str, int] = Field(description="Starting position of results", validation_alias=AliasPath('esearchresult', 'retstart'))
    id_list: List[str] = Field(description="List of taxonomy IDs found", validation_alias=AliasPath('esearchresult', 'idlist'))

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
    
    @model_validator(mode='before')
    def extract_nested_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract nested data from the NCBI esummary response"""
        if not isinstance(data, dict):
            return data
            
        result = data.get('result')
        if not isinstance(result, dict):
            return data
            
        # Extract uids from nested structure
        uids = result.get('uids', [])
        
        # Create a new result dict that only contains taxonomy records
        tax_records = {}
        for uid in uids:
            if uid in result:
                tax_records[uid] = result[uid]
        
        # Return restructured data
        return {
            'uids': uids,
            'result': tax_records
        } 