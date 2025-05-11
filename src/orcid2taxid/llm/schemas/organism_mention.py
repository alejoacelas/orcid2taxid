from typing import List, Literal
from pydantic import BaseModel, Field

class OrganismMentionLLM(BaseModel):
    """Model for a single organism found in the paper."""
    name: str = Field(..., description="Original name of the organism as found in the text")
    controlled_agent: Literal["Yes", "No"] = Field(..., description="Whether the organism is on the provided controlled agent list")
    work_type: Literal["Direct wet-lab", "Computational", "Undetermined"] = Field(..., description="Type of work done with the organism")
    searchable_term: str = Field(..., description="Searchable term for NCBI database if different from name")
    quote: str = Field(..., description="Publication quote providing evidence of organism being worked with (max 140 chars)")

class OrganismMentionListLLM(BaseModel):
    """Model for the complete organism extraction response."""
    organisms: List[OrganismMentionLLM] = Field(default_factory=list, description="List of organisms found in the paper")
    justification: str = Field(..., description="One-sentence summary explaining the findings")