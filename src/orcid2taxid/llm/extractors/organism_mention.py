from typing import List
from pydantic import ValidationError
from aiolimiter import AsyncLimiter

from orcid2taxid.publication.schemas import PublicationRecord
from orcid2taxid.llm.schemas.organism_mention import OrganismMention,PublicationOrganisms
from orcid2taxid.core.logging import get_logger, log_event
from orcid2taxid.llm.exceptions import LLMAPIError, LLMValidationError
from orcid2taxid.llm.utils import load_instructor_client, load_prompt

logger = get_logger(__name__)

@log_event(__name__)
async def extract_organisms_from_abstract(paper: PublicationRecord) -> List[OrganismMention]:
    """
    Uses an LLM to detect organism names from text with structured output.
    
    :param paper: The paper metadata containing title and abstract
    :return: List of recognized organism names.
    """
    try:
        # Initialize client and load prompt
        model = "gemini-2.0-flash"
        client = load_instructor_client(model)
        prompt = load_prompt("organism_extraction/abstract_only.txt")
        
        # Apply rate limiting - 100 requests per minute
        async with AsyncLimiter(100, 60):
            response = await client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_model=PublicationOrganisms,
                max_retries=2,
                context={
                    "pathogen_list": load_prompt("organism_extraction/pathogen_list.txt"),
                    "PublicationRecord": paper.model_dump_json()
                }
            )
        
        # Convert to OrganismMention objects using the model's method
        return response.to_mentions()
        
    except Exception as e:
        logger.error("Error extracting organisms from paper: %s", str(e))
        if isinstance(e, ValidationError):
            raise LLMValidationError(
                message="Failed to validate LLM response",
                validation_error=e,
                details={"publication_id": paper.id if hasattr(paper, "id") else None}
            ) from e
        raise LLMAPIError(
            message="Failed to extract organisms from paper",
            provider="gemini",
            details={"error": str(e), "publication_id": paper.id if hasattr(paper, "id") else None}
        ) from e 