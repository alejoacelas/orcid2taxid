from typing import List, Dict, Type, get_type_hints, get_args
from pathlib import Path
from orcid2taxid.core.models.schemas import OrganismMention, PaperMetadata, PaperClassificationMetadata
from orcid2taxid.core.utils.llm import LLMClient
from orcid2taxid.core.utils.data import load_yaml_data, render_prompt
from orcid2taxid.core.utils.llm import extract_tagged_content
import json

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
        # Check for the "No organisms" response
        if "No organisms from the provided list were directly worked with in this study" in response_text:
            return {
                "organisms": [],
                "justification": "No organisms from the provided list were found in the study."
            }
            
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

    def _generate_classification_prompt(self) -> str:
        """
        Generate the classification prompt description from the schema.
        
        :return: String containing the formatted prompt description
        """
        prompt_lines = []
        
        # Get the model fields and their types
        model_fields = PaperClassificationMetadata.model_fields
        
        # Process each field
        for field_name, field in model_fields.items():
            if field_name == "additional_notes":
                continue  # Skip additional notes as it's not a classification
                
            # Get the field type and description
            field_type = field.annotation
            description = field.description
            
            # Handle List types
            if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                base_type = get_args(field_type)[0]
                values = get_args(base_type)
                prompt_lines.append(f"\na) {description} ({field_name}):")
                for value in values:
                    prompt_lines.append(f"- \"{value}\"")
            else:
                # Handle single value types
                values = get_args(field_type)
                prompt_lines.append(f"\na) {description} ({field_name}):")
                for value in values:
                    prompt_lines.append(f"- \"{value}\"")
        
        return "\n".join(prompt_lines)

    def extract_classification_from_abstract(self, paper: PaperMetadata) -> PaperClassificationMetadata:
        """
        Uses an LLM to classify various aspects of the paper based on its content.
        
        :param paper: The paper metadata containing title and abstract
        :return: PaperClassificationMetadata object with classifications
        """
        template_data = {
            "paper_content": f"Title: {paper.title}\n\nAbstract: {paper.abstract}",
            "classification_description": self._generate_classification_prompt()
        }
        
        prompt = render_prompt(PROMPT_DIR, "classification_extraction.txt", **template_data)
        response_text = self.llm.call(prompt)
        parsed_result = self._parse_classification_response(response_text)
        
        return PaperClassificationMetadata(**parsed_result)

    def _parse_classification_response(self, response_text: str) -> Dict:
        """
        Parse the LLM response for paper classification.
        
        :param response_text: The raw response text from the LLM
        :return: Dictionary containing parsed classifications
        """
        classification_section = extract_tagged_content(response_text, "classification")
        justification = extract_tagged_content(response_text, "justification")
        
        if not classification_section:
            raise ValueError("No classification section found in LLM response")
            
        try:
            # Parse the JSON classification section
            classification_dict = json.loads(classification_section)
            
            # Validate required fields
            required_fields = {
                "wet_lab_work", "bsl_level", "dna_use", 
                "novel_sequence_experience", "dna_type"
            }
            missing_fields = required_fields - set(classification_dict.keys())
            if missing_fields:
                raise ValueError(f"Missing required fields in classification: {missing_fields}")
                
            return classification_dict
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse classification JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error processing classification response: {e}") 