from pydantic import Field
from typing import Optional, List
from orcid2taxid.llm.schemas.organism_mention import OrganismMention
from orcid2taxid.organism.schemas.ncbi import NCBITaxonomyInfo

class OrganismMentionWithTaxid(OrganismMention):
    """Represents a mention of an organism in text with additional taxid information"""
    taxid: Optional[int] = Field(description="NCBI Taxonomy ID")
    scientific_name: Optional[str] = Field(description="Scientific name of the organism")
    rank: Optional[str] = Field(description="Taxonomic rank of the organism")
    lineage: Optional[List[str]] = Field(description="Full taxonomic lineage of the organism")

    @classmethod
    def from_taxonomy_info(cls, mention: OrganismMention, taxonomy_info: NCBITaxonomyInfo) -> "OrganismMentionWithTaxid":
        """Create an OrganismMentionWithTaxid from an OrganismMention and NCBITaxonomyInfo"""
        return cls(
            **mention.model_dump(),
            taxid=taxonomy_info.taxid,
            scientific_name=taxonomy_info.scientific_name,
            rank=taxonomy_info.rank,
            lineage=taxonomy_info.lineage
        )