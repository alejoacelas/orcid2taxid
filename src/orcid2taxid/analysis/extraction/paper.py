from typing import List, Dict, Type, get_type_hints, get_args
from pathlib import Path
import asyncio
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

    async def extract_organisms_from_abstract(self, paper: PaperMetadata) -> List[OrganismMention]:
        """
        Uses an LLM to detect organism names from text.
        
        :param paper: The paper metadata containing title and abstract
        :return: List of recognized organism names.
        """
        template_data = {
            "pathogen_list": "\n".join(self.pathogens),
            "paper_content": f"Title: {paper.title}\n\nAbstract: {paper.abstract}"
        }
        
        prompt = render_prompt(PROMPT_DIR, "abstract_only_organism_extraction.txt", **template_data)
        response_text = await self.llm.call_async(prompt)
        parsed_result = self._parse_organism_response(response_text)
        
        organisms = []
        for org in parsed_result["organisms"]:
            organisms.append(OrganismMention(
                original_name=org["original_name"],
                searchable_name=org["searchable_name"],
                context=org["evidence"],
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
        if "<no_organisms_found>" in response_text:
            return {
                "organisms": [],
                "justification": extract_tagged_content(response_text, "justification") or "No organisms from the provided list were found in the study."
            }
            
        organisms = []
        # Extract all organism blocks
        organism_blocks = response_text.split("<organism>")[1:]  # Skip the first split as it's before any organism tag
        
        for block in organism_blocks:
            # Extract fields from the XML block
            name = extract_tagged_content(block, "name")
            on_list = extract_tagged_content(block, "on_list")
            work_type = extract_tagged_content(block, "work_type")
            searchable_term = extract_tagged_content(block, "searchable_term")
            evidence = extract_tagged_content(block, "evidence")
            
            if name:  # Only process if we have at least a name
                organisms.append({
                    "original_name": name.strip(),
                    "searchable_name": searchable_term.strip() if searchable_term else name.strip(),
                    "on_list": on_list.strip() if on_list else "No",
                    "work_type": work_type.strip() if work_type else "Undetermined",
                    "evidence": evidence.strip() if evidence else ""
                })
        
        return {
            "organisms": organisms,
            "justification": extract_tagged_content(response_text, "justification") or ""
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

    async def extract_classification_from_abstract(self, paper: PaperMetadata) -> PaperClassificationMetadata:
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
        response_text = await self.llm.call_async(prompt)
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
            
    async def process_paper(self, paper: PaperMetadata) -> PaperMetadata:
        """
        Process a paper asynchronously, extracting organisms and classification.
        
        :param paper: The paper metadata to process
        :return: Updated paper metadata with organisms and classification
        """
        # Run both extractions in parallel
        organisms_task = self.extract_organisms_from_abstract(paper)
        classification_task = self.extract_classification_from_abstract(paper)
        
        # Await both tasks
        organisms, classification = await asyncio.gather(organisms_task, classification_task)
        
        # Update the paper with the results
        paper.organisms = organisms
        paper.classification = classification
        
        return paper 