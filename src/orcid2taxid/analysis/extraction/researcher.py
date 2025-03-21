from typing import Dict
from pathlib import Path
from orcid2taxid.core.models.schemas import ResearcherMetadata
from orcid2taxid.core.utils.llm import LLMClient
from orcid2taxid.core.utils.data import render_prompt
from orcid2taxid.core.utils.llm import extract_tagged_content
from collections import Counter

PROMPT_DIR = Path(__file__).parent / "prompts"
DATA_DIR = Path(__file__).parent / "data"

class ResearcherExtractor:
    """
    Uses an LLM to extract and generate information about researchers.
    """
    def __init__(self, model: str = "claude-3-7-sonnet-20250219"):
        """
        :param model: Name of the LLM model to be used (only Anthropic models are supported for now).
        """
        self.llm = LLMClient(model=model)

    def generate_researcher_bio(self, researcher: ResearcherMetadata) -> Dict[str, str]:
        """
        Generates a biographical summary of a researcher based on their metadata and publications.
        
        :param researcher: ResearcherMetadata object containing researcher information
        :return: Dictionary containing generated bio and supporting information
        """
        # Prepare researcher data for the prompt
        recent_papers = sorted(
            [p for p in researcher.publications if p.publication_date],
            key=lambda x: x.publication_date,
            reverse=True
        )[:5]  # Get 5 most recent papers
        
        # Get most common subjects/keywords
        subjects = Counter([s for s in researcher.subjects]).most_common(5)
        keywords = Counter([k for k in researcher.keywords]).most_common(5)
        
        template_data = {
            "full_name": researcher.full_name,
            "biography": researcher.biography or "",
            "recent_papers": "\n".join([f"- {p.title}" for p in recent_papers]),
            "subjects": ", ".join([s[0] for s in subjects]),
            "keywords": ", ".join([k[0] for k in keywords]),
            "total_publications": len(researcher.publications),
            "affiliations": "\n".join([
                f"- {aff.institution_name} ({aff.role or 'Unknown role'})"
                for aff in researcher.affiliations
            ])
        }
        
        prompt = render_prompt(PROMPT_DIR, "researcher_bio.txt", **template_data)
        response_text = self.llm.call(prompt)
        
        return self._parse_bio_response(response_text)
    
    def _parse_bio_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse the LLM response for researcher bio generation.
        
        :param response_text: The raw response text from the LLM
        :return: Dictionary containing parsed bio sections
        """
        return {
            "short_bio": extract_tagged_content(response_text, "short_bio") or "",
            "research_focus": extract_tagged_content(response_text, "research_focus") or "",
            "achievements": extract_tagged_content(response_text, "achievements") or "",
            "justification": extract_tagged_content(response_text, "justification") or ""
        }
