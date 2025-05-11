from typing import List, Optional
from pydantic import Field
from orcid2taxid.llm.schemas.organism_mention import OrganismMentionLLM, OrganismMentionListLLM
from orcid2taxid.taxonomy.schemas.base import OrganismTaxonomy

class OrganismMention(OrganismMentionLLM):
    taxonomy: Optional[OrganismTaxonomy] = Field(None, description="Taxonomy information for the organism")

class OrganismMentionList(OrganismMentionListLLM):
    organisms: List[OrganismMention] = Field(default_factory=list, description="List of organisms found in the paper")
    
    @classmethod
    def from_llm_response(cls, llm_response: OrganismMentionListLLM) -> "OrganismMentionList":
        return cls(
            organisms=[OrganismMention(**organism.model_dump()) for organism in llm_response.organisms],
            justification=llm_response.justification
        )
