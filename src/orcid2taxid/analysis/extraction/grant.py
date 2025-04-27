from typing import List, Dict
from pathlib import Path
from orcid2taxid.grants.schemas import GrantRecord
from orcid2taxid.core.utils.llm import LLMClient
from orcid2taxid.core.utils.data import render_prompt
from orcid2taxid.core.utils.llm import extract_tagged_content

PROMPT_DIR = Path(__file__).parent / "prompts"
DATA_DIR = Path(__file__).parent / "data"

class GrantExtractor:
    """
    Uses an LLM to extract and standardize terms from grant abstracts.
    """
    def __init__(self):
        """
        :param model: Name of the LLM model to be used (only Anthropic models are supported for now).
        """
        self.llm = LLMClient()

    def extract_terms_from_abstract(self, grant: GrantRecord) -> List[str]:
        """
        Uses an LLM to detect key terms from grant title and abstract.
        
        :param grant: GrantRecord object containing grant information
        :return: List of key terms extracted from the grant
        """
        template_data = {
            "grant_content": f"Title: {grant.title}\n\nAbstract: {grant.abstract}"
        }
        
        prompt = render_prompt(PROMPT_DIR, "grant_terms.txt", **template_data)
        response_text = self.llm.call(prompt)
        parsed_result = self._parse_terms_response(response_text)
        
        return parsed_result["terms"]

    def _parse_terms_response(self, response_text: str) -> Dict[str, List[str]]:
        """
        Parse the LLM response for term extraction.
        
        :param response_text: The raw response text from the LLM
        :return: Dictionary containing parsed terms and justification
        """
        terms_section = extract_tagged_content(response_text, "key_terms")
        justification = extract_tagged_content(response_text, "justification")
        
        terms = []
        if terms_section:
            for line in terms_section.split("\n"):
                if line.strip():
                    terms.append(line.strip())
        
        return {
            "terms": terms,
            "justification": justification or ""
        } 