from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List, Any

class EmailInfo(BaseModel):
    """Represents an email address with its metadata"""
    address: str
    primary: bool = False
    
class ResearcherID(BaseModel):
    """Represents a person's ID"""
    given_name: str = None
    family_name: str = None
    
    credit_name: Optional[str] = None
    orcid: Optional[str] = None
    emails: List[EmailInfo] = Field(default_factory=list)
    
    def __post_init__(self):
        if not self.orcid:
            if not self.emails:
                raise ValueError("Either ORCID or email must be provided")
    
class ExternalReference(BaseModel):
    """Represents an external reference"""
    url: str
    name: Optional[str] = None
    source: Optional[str] = None

class ResearcherDescription(BaseModel):
    """Represents a person's description"""
    text: str = ""
    
    def add_section(self, title: str, text: str) -> None:
        """Add a section to the description"""
        self.text += f"## {title}\n{text}\n\n"
    
class DatetimeSerializableBaseModel(BaseModel):
    """Base model with custom JSON serialization configuration"""
    model_config = ConfigDict(
        json_schema_extra={
            "json_serializers": {
                datetime: lambda dt: dt.isoformat() if dt else None
            }
        }
    )

class InstitutionalAffiliation(DatetimeSerializableBaseModel):
    """Represents an author's affiliation with an institution"""
    institution: str
    department: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
class ResearcherProfile(BaseModel):
    """Core customer profile information"""
    researcher_id: ResearcherID = Field(default_factory=ResearcherID)
    
    educations: List[InstitutionalAffiliation] = Field(default_factory=list)
    employments: List[InstitutionalAffiliation] = Field(default_factory=list)
    
    description: ResearcherDescription = Field(default_factory=ResearcherDescription)
    external_references: List[ExternalReference] = Field(default_factory=list)