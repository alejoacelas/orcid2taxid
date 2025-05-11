from typing import List
from pydantic import ValidationError
from aiolimiter import AsyncLimiter

from orcid2taxid.publication.schemas import PublicationRecord
from orcid2taxid.llm.schemas.base import OrganismMentionList
from orcid2taxid.llm.schemas.organism_mention import OrganismMentionListLLM
from orcid2taxid.core.logging import get_logger, log_event
from orcid2taxid.llm.exceptions import LLMAPIError, LLMValidationError
from orcid2taxid.llm.utils import load_instructor_client, load_prompt

logger = get_logger(__name__)

@log_event(__name__)
async def extract_organisms_from_publication(publication: PublicationRecord) -> OrganismMentionList:
    """
    Uses an LLM to detect organism names from text with structured output.
    
    :param paper: The paper metadata containing title and abstract
    :return: List of recognized organism names.
    """
    try:
        # Initialize client and load prompt
        model = "gemini-2.0-flash"
        client = load_instructor_client(model)
        prompt = load_prompt("organism_mention/abstract_only.txt")
        context = {
            "pathogen_list": load_prompt("organism_mention/pathogen_list.txt"),
            "PublicationRecord": publication.model_dump()
        }
       
        # Apply rate limiting - 100 requests per minute
        async with AsyncLimiter(100, 60):
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_model=OrganismMentionListLLM,
                max_retries=2,
                context=context
            )
        
        return OrganismMentionList.from_llm_response(response)
        
    except Exception as e:
        logger.error("Error extracting organisms from paper: %s", str(e))
        if isinstance(e, ValidationError):
            raise LLMValidationError(
                message="Failed to validate LLM response",
                validation_error=e,
                details={"publication_id": publication.id if hasattr(publication, "id") else None}
            ) from e
        raise LLMAPIError(
            message="Failed to extract organisms from paper",
            provider="gemini",
            details={"error": str(e), "publication_id": publication.id if hasattr(publication, "id") else None}
        ) from e 