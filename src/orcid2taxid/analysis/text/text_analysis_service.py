from typing import List
from orcid2taxid.core.models.schemas import OrganismMention

class LLMAnalyzer:
    """
    Uses an LLM to extract and standardize organisms from text.
    """
    def __init__(self, model_name: str):
        """
        :param model_name: Name or path of the LLM model to be used.
        """
        pass

    def analyze_text_for_organisms(self, text: str) -> List[OrganismMention]:
        """
        Uses an LLM to detect organism names from text.
        :param text: The text to analyze (abstract or full text).
        :return: List of recognized organism names.
        """
        pass
    
    def standardize_names_for_ncbi_search(self, names: List[OrganismMention]) -> List[OrganismMention]:
        """
        Standardizes organism names for NCBI taxonomy searches.
        :param names: List of organism names.
        :return: List of standardized names.
        """
        pass
    