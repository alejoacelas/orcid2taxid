from pydantic import Field, BaseModel
from typing import Optional, List
from orcid2taxid.taxonomy.schemas.ncbi import NCBITaxRecord

class OrganismTaxonomy(BaseModel):
    """Represents a mention of an organism in text with additional taxid information"""
    taxid: Optional[int] = Field(None, description="NCBI Taxonomy ID")
    scientific_name: Optional[str] = Field(None, description="Scientific name of the organism")
    rank: Optional[str] = Field(None, description="Taxonomic rank of the organism")
    lineage: Optional[List[str]] = Field(None, description="Full taxonomic lineage of the organism")
        
    @classmethod
    def from_ncbi_taxonomy_record(cls, tax_record: NCBITaxRecord) -> "OrganismTaxonomy":
        """
        Create an OrganismTaxonomy directly from a NCBITaxRecord
        
        Handles parsing of lineage string and field conversions.
        
        :param tax_record: NCBITaxRecord from API response
        :return: OrganismTaxonomy instance
        """
        lineage = None
        if tax_record.lineage:
            lineage = [item.strip() for item in tax_record.lineage.split(';')]
            
        return cls(
            taxid=int(tax_record.uid) if tax_record.uid else None,
            scientific_name=tax_record.scientific_name,
            rank=tax_record.rank,
            lineage=lineage
        )
