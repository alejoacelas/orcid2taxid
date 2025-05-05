from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class OrganismMention(BaseModel):
    """Model for a single organism found in the paper."""
    name: str = Field(..., description="Original name of the organism as found in the text")
    on_list: str = Field(..., description="Whether the organism is on the provided pathogen list (Yes/No)")
    work_type: Literal["Direct wet-lab", "Computational", "Undetermined"] = Field(..., description="Type of work done with the organism")
    searchable_term: Optional[str] = Field(None, description="Searchable term for NCBI database if different from name")
    evidence: str = Field(..., description="Text snippet providing evidence of organism being worked with (max 140 chars)")

class PublicationOrganisms(BaseModel):
    """Model for the complete organism extraction response."""
    organisms: List[OrganismMention] = Field(default_factory=list, description="List of organisms found in the paper")
    justification: str = Field(..., description="One-sentence summary explaining the findings")