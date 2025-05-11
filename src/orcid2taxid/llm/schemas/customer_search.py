from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class SourceInformation(BaseModel):
    """Model for a single source of information used to answer a question."""
    url: str = Field(..., description="URL or reference to the source")
    summary: str = Field(..., description="Short summary of the information from the source")
    quote: str = Field(..., description="Verbatim quote from the original source (max 280 characters)")


class ResearchOutput(BaseModel):
    """Model for a significant research publication, patent, or technical output."""
    title: str = Field(..., description="Title of the research output")
    url: str = Field(..., description="URL or reference to the research output")
    organisms_used: List[str] = Field(default_factory=list, description="Types of organisms or biological materials used")
    techniques: List[str] = Field(default_factory=list, description="Techniques employed in the research")
    biosafety_considerations: Optional[str] = Field(None, description="Any biosafety considerations mentioned")
    summary: str = Field(..., description="Brief summary of the research output")


class CustomerSearchLLM(BaseModel):
    """Model for the complete customer search response."""
    # Institution/customer information
    research_focus_sources: List[SourceInformation] = Field(
        ..., 
        description="Sources about the primary research focus or business area"
    )
    
    biosafety_level_sources: List[SourceInformation] = Field(
        ..., 
        description="Sources about the highest biosafety level (BSL) facility documented"
    )
    highest_bsl: Optional[str] = Field(
        None, 
        description="Highest biosafety level identified (e.g., 'BSL-1', 'BSL-2', 'BSL-3', 'BSL-4', or 'Unknown')"
    )
    
    controlled_agents_sources: List[SourceInformation] = Field(
        ..., 
        description="Sources about work with agents on control lists"
    )
    has_worked_with_controlled_agents: Literal["Yes", "No", "Unknown"] = Field(
        ..., 
        description="Whether the institution/customer has worked with controlled agents"
    )
    
    # Customer-specific information
    customer_role_sources: List[SourceInformation] = Field(
        ..., 
        description="Sources about the customer's role and level of responsibility"
    )
    handles_controlled_agents: Literal["Yes", "No", "Unknown"] = Field(
        ..., 
        description="Whether there's evidence the customer handles controlled biological agents"
    )
    
    significant_outputs: List[ResearchOutput] = Field(
        ..., 
        description="Up to three significant research publications, patents, or technical outputs",
        max_items=3
    )
    
    # Overall assessment
    summary: str = Field(
        ..., 
        description="Brief overall summary of findings about the customer and institution"
    )
