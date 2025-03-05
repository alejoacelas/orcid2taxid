from typing import List
import os
from dotenv import load_dotenv
import anthropic
import logging
from orcid2taxid.core.models.schemas import OrganismMention, PaperMetadata

# Set up logging
logger = logging.getLogger(__name__)

# List of pandemic potential pathogens to look for in papers
PATHOGEN_LIST = [
    "SARS-CoV-2",
    "Ebola virus",
    "Zika virus",
    "Influenza A virus",
    "Influenza B virus",
    "MERS-CoV",
    "SARS-CoV",
    "Nipah virus",
    "Hendra virus",
    "Lassa virus",
    "Marburg virus",
    "Yellow fever virus",
    "Dengue virus",
    "West Nile virus",
    "Japanese encephalitis virus",
    "Tick-borne encephalitis virus",
    "Crimean-Congo hemorrhagic fever virus",
    "Rift Valley fever virus",
    "Chikungunya virus",
    "Hantavirus",
    "Monkeypox virus",
    "Smallpox virus",
    "Bacillus anthracis",
    "Yersinia pestis",
    "Francisella tularensis",
    "Burkholderia mallei",
    "Burkholderia pseudomallei",
    "Coxiella burnetii",
    "Rickettsia prowazekii",
    "Brucella species",
    "Clostridium botulinum",
    "Vibrio cholerae",
    "Shigella species",
    "Salmonella enterica",
    "Escherichia coli O157:H7",
    "Mycobacterium tuberculosis",
    "Streptococcus pneumoniae",
    "Staphylococcus aureus",
    "Klebsiella pneumoniae",
    "Acinetobacter baumannii",
    "Pseudomonas aeruginosa",
    "Enterococcus faecium",
    "Enterococcus faecalis",
    "Candida auris",
    "Aspergillus fumigatus",
    "Cryptococcus neoformans",
    "Histoplasma capsulatum",
    "Coccidioides immitis",
    "Blastomyces dermatitidis"
]

class LLMOrganismExtractor:
    """
    Uses an LLM to extract and standardize organisms from text.
    """
    def __init__(self, model_name: str = "claude-3-7-sonnet-20250219"):
        """
        :param model_name: Name or path of the LLM model to be used.
        """
        load_dotenv()
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model_name = model_name

    def extract_organisms_from_abstract(self, paper_metadata: PaperMetadata) -> List[OrganismMention]:
        """
        Uses an LLM to detect organism names from text.
        
        :param paper_metadata: The paper metadata containing title and abstract.
        :return: List of recognized organism names.
        """
        # Combine title and abstract for analysis
        text_to_analyze = f"Title: {paper_metadata.title}\n\nAbstract: {paper_metadata.abstract}"
        
        # Create the prompt with the pathogen list and paper content
        prompt = f"""You will be analyzing a scientific paper to identify organisms from a list of pandemic potential pathogens that were directly worked with in the study. Follow these steps carefully:

1. First, you will be provided with a list of pandemic potential pathogens. This list will be enclosed in <pathogen_list> tags.

<pathogen_list>
{PATHOGEN_LIST}
</pathogen_list>

2. Next, you will be given the title and abstract of a scientific paper. This content will be enclosed in <scientific_paper> tags.

<scientific_paper>
{text_to_analyze}
</scientific_paper>

3. Carefully read through the title and abstract, paying close attention to mentions of organisms that are directly manipulated, cultured, or experimented upon in the study.

4. To determine if an organism was directly worked with, consider the following criteria:
   a. The organism is mentioned in the context of laboratory procedures, experiments, or manipulations.
   b. There are specific details about how the organism was handled, cultured, or analyzed.
   c. The paper presents original data or results related to the organism.
   d. The organism is central to the study's objectives or hypotheses.

5. Do not include organisms that are merely mentioned in passing, used as comparisons, or referenced from other studies without direct experimentation in the current paper.

6. Cross-reference the organisms you've identified as being directly worked with against the provided list of pandemic potential pathogens.

7. Prepare your output in the following format:
   a. If no organisms from the pathogen list were directly worked with in the paper, state "No organisms from the provided list were directly worked with in this study."
   b. If one or more organisms from the list were directly worked with, list them in <organisms_worked_with> tags, with each organism on a new line.
   c. Make sure that the organisms are searchable in the NCBI database. If the extracted organism name is not immediately searchable, translate it to a searchable term. List the searchable term next to the original name.

8. After the list (or statement of no organisms found), provide a brief justification for your findings in <justification> tags. Explain why you included or excluded certain organisms based on the paper's content.

Present your final output in this structure:

<output>
<organisms_worked_with>
[List organisms here, one per line]
</organisms_worked_with>

<justification>
[Provide your justification here]
</justification>
</output>"""

        # Call the Claude API
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=20000,
            temperature=1,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Log the full response for debugging
        response_text = message.content[0].text

        # Parse the response and create OrganismMention objects
        organisms = []
        
        # Extract the organisms section
        if "<organisms_worked_with>" in response_text:
            organisms_section = response_text.split("<organisms_worked_with>")[1].split("</organisms_worked_with>")[0].strip()
            justification = response_text.split("<justification>")[1].split("</justification>")[0].strip()
            
            # Process each organism line
            for line in organisms_section.split("\n"):
                if line.strip():
                    # Split the line into original and searchable names if both are provided
                    parts = line.strip().split(" -> ")
                    if len(parts) == 2:
                        original_name, searchable_name = parts
                    else:
                        original_name = searchable_name = parts[0]
                    
                    # Create OrganismMention with all required fields
                    organisms.append(OrganismMention(
                        original_name=original_name.strip(),
                        searchable_name=searchable_name.strip(),
                        context="",  # Default empty context
                        confidence=1.0,  # Default confidence
                        justification=justification,
                        taxonomy_info=None  # Will be populated later by taxid lookup
                    ))

        return organisms
    