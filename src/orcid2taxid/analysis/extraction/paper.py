from typing import List, Dict
from pathlib import Path
from orcid2taxid.core.models.schemas import OrganismMention, PaperMetadata
from orcid2taxid.core.utils.llm import LLMClient
from orcid2taxid.core.utils.data import load_yaml_data, render_prompt
from orcid2taxid.core.utils.llm import extract_tagged_content

PROMPT_DIR = Path(__file__).parent / "prompts"
DATA_DIR = Path(__file__).parent / "data"

class PaperExtractor:
    """
    Uses an LLM to extract and standardize organisms from text.
    """
    def __init__(self, model: str = "claude-3-7-sonnet-20250219"):
        """
        :param model: Name of the LLM model to be used (only Anthropic models are supported for now).
        """
        self.llm = LLMClient(model=model)
        self.pathogens = load_yaml_data(DATA_DIR / "pathogens.yaml")["pathogens"]

    def extract_organisms_from_abstract(self, paper: PaperMetadata) -> List[OrganismMention]:
        """
        Uses an LLM to detect organism names from text.
        
        :param title: The title of the paper.
        :param abstract: The abstract of the paper.
        :return: List of recognized organism names.
        """
        template_data = {
            "pathogen_list": "\n".join(self.pathogens),
            "paper_content": f"Title: {paper.title}\n\nAbstract: {paper.abstract}"
        }
        
        prompt = render_prompt(PROMPT_DIR, "organism_extraction.txt", **template_data)
        response_text = self.llm.call(prompt)
        parsed_result = self._parse_organism_response(response_text)
        
        organisms = []
        for org in parsed_result["organisms"]:
            organisms.append(OrganismMention(
                original_name=org["original_name"],
                searchable_name=org["searchable_name"],
                context="",  # Default empty context
                confidence=1.0,  # Default confidence
                justification=parsed_result["justification"],
            ))
        
        return organisms

    def _parse_organism_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse the LLM response for organism extraction.
        
        :param response_text: The raw response text from the LLM
        :return: Dictionary containing parsed organisms and justification
        """
        organisms_section = extract_tagged_content(response_text, "organisms_worked_with")
        justification = extract_tagged_content(response_text, "justification")
        
        organisms = []
        if organisms_section:
            for line in organisms_section.split("\n"):
                if line.strip():
                    # Split the line into original and searchable names if both are provided
                    parts = line.strip().split(" -> ")
                    if len(parts) == 2:
                        original_name, searchable_name = parts
                    else:
                        original_name = searchable_name = parts[0]
                    
                    organisms.append({
                        "original_name": original_name.strip(),
                        "searchable_name": searchable_name.strip()
                    })
        
        return {
            "organisms": organisms,
            "justification": justification or ""
        } 