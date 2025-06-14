from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class EmailInfo(BaseModel):
    """Represents an email address with its metadata"""
    address: str
    primary: bool = False

class ResearcherID(BaseModel):
    """Represents a person's ID with required contact information"""
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    credit_name: Optional[str] = None
    orcid: Optional[str] = None
    emails: List[EmailInfo] = Field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        """Get the full name by combining given_name and family_name"""
        return f"{self.given_name} {self.family_name}"
    
    def is_same_person(self, other: 'ResearcherID') -> bool:
        """
        Check if this ResearcherID represents the same person as another ResearcherID.
        
        Args:
            other: Another ResearcherID instance to compare with
            
        Returns:
            bool: True if the IDs represent the same person, False otherwise
        """
        # Match by ORCID if available
        if self.orcid and other.orcid and self.orcid == other.orcid:
            return True
            
        # Match by email if available
        if self.emails and other.emails:
            self_emails = {email.address for email in self.emails}
            other_emails = {email.address for email in other.emails}
            if self_emails.intersection(other_emails):
                return True
                
        # Match by name if available
        if self.credit_name and other.credit_name and self.credit_name == other.credit_name:
            return True
            
        # Match by given/family name if available
        if (self.given_name and self.family_name and 
            other.given_name and other.family_name and
            self.given_name == other.given_name and 
            self.family_name == other.family_name):
            return True
            
        return False

class ExternalReference(BaseModel):
    """Represents an external reference"""
    url: str
    name: Optional[str] = None
    source: Optional[str] = None

class ResearcherDescription(BaseModel):
    """Represents a person's description"""
    text: str = ""
    
    def extend(self, title: str, text: str) -> None:
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
    
    def format_time_range(self) -> str:
        """Format the time range for this affiliation.
        
        Returns:
            str: Formatted time range string (e.g., "(2020 - Present)" or "(2018 - 2022)")
        """
        if not self.start_date:
            return ""
            
        start_year = self.start_date.strftime('%Y')
        if not self.end_date:
            return f"({start_year} - Present)"
        else:
            end_year = self.end_date.strftime('%Y')
            return f"({start_year} - {end_year})"
    
    def format_role(self) -> str:
        """Format the role and department for this affiliation.
        
        Returns:
            str: Formatted role string (e.g., "Professor, Computer Science")
        """
        parts = []
        if self.role:
            parts.append(self.role)
        if self.department:
            parts.append(self.department)
        return ", ".join(parts) if parts else ""
    
class ResearcherProfile(BaseModel):
    """Core customer profile information"""
    researcher_id: ResearcherID = Field(default_factory=ResearcherID)
    
    educations: List[InstitutionalAffiliation] = Field(default_factory=list)
    employments: List[InstitutionalAffiliation] = Field(default_factory=list)
    
    description: ResearcherDescription = Field(default_factory=ResearcherDescription)
    external_references: List[ExternalReference] = Field(default_factory=list)