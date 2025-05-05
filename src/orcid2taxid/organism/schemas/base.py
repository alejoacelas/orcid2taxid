from pydantic import BaseModel, Field
from typing import Optional

class OrganismMention(BaseModel):
    """Represents a mention of an organism in text"""
    original_name: str = Field(description="Original organism name as found in text")
    searchable_name: str = Field(description="Searchable organism name for NCBI database")
    context: Optional[str] = Field(description="Context in which the organism was mentioned")
    confidence: Optional[float] = Field(description="Confidence score of the extraction")
    justification: Optional[str] = Field(description="Explanation of why this organism was included") 