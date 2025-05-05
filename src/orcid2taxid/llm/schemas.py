from typing import List, Optional
from pydantic import BaseModel, Field

class OrganismMention(BaseModel):
    """Schema for a single organism mention in the LLM response"""
    original_name: str = Field(..., description="Original organism name as found in the text")
    searchable_name: str = Field(..., description="Searchable name for NCBI database lookup")
    on_list: str = Field(..., description="Whether the organism is on the provided pathogen list")
    work_type: str = Field(..., description="Type of work done with the organism")
    evidence: str = Field(..., description="Text snippet providing evidence of organism mention")

class OrganismExtractionResponse(BaseModel):
    """Schema for the complete organism extraction LLM response"""
    organisms: List[OrganismMention] = Field(default_factory=list, description="List of identified organisms")
    justification: str = Field(..., description="Justification for the extraction results")
    no_organisms_found: Optional[bool] = Field(None, description="Flag indicating no organisms were found")

class PaperClassificationMetadata(BaseModel):
    """Schema for paper classification metadata"""
    wet_lab_work: str = Field(..., description="Whether the paper involves wet lab work")
    bsl_level: str = Field(..., description="Highest biosafety level mentioned")
    dna_use: List[str] = Field(..., description="List of DNA usage types")
    novel_sequence_experience: str = Field(..., description="Researcher's experience with novel sequences")
    dna_type: List[str] = Field(..., description="Types of synthetic DNA used")

class PaperClassificationResponse(BaseModel):
    """Schema for the paper classification LLM response"""
    wet_lab_work: str = Field(..., description="Whether the paper involves wet lab work")
    bsl_level: str = Field(..., description="Highest biosafety level mentioned")
    dna_use: List[str] = Field(..., description="List of DNA usage types")
    novel_sequence_experience: str = Field(..., description="Researcher's experience with novel sequences")
    dna_type: List[str] = Field(..., description="Types of synthetic DNA used")
    justification: str = Field(..., description="Justification for the classification results") 