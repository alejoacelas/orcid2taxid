from typing import List
from pydantic import ValidationError
from aiolimiter import AsyncLimiter

from orcid2taxid.researcher.schemas import CustomerProfile
from orcid2taxid.llm.schemas.base import CustomerSearch
from orcid2taxid.llm.schemas.customer_search import CustomerSearchLLM
from orcid2taxid.core.logging import get_logger, log_event
from orcid2taxid.llm.exceptions import LLMAPIError, LLMValidationError
from orcid2taxid.llm.utils import load_instructor_client, load_prompt

logger = get_logger(__name__)

@log_event(__name__)
async def search_customer_information(customer: str | CustomerProfile) -> CustomerSearch:
    """
    Uses an LLM to search for information about a customer for screening purposes.
    
    :param customer: The customer profile containing identifying information
    :return: Structured information about the customer from web search
    """
    try:
        # Initialize client and load prompt
        # model = "o3"
        # model = "gpt-4o"
        model = "gemini-2.5-pro-preview-05-06"
        client = load_instructor_client(model)
        if isinstance(customer, str):
            prompt = load_prompt("customer_search/o3_search_free_text_profile.txt")
            context = {"customer_profile": customer}
        elif isinstance(customer, CustomerProfile):
            prompt = load_prompt("customer_search/o3_search.txt")
            context = {"customer_profile": customer.model_dump()}
        else:
            raise ValueError("Invalid customer type")
       
        # Apply rate limiting - 3 requests per minute
        async with AsyncLimiter(3, 60):
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_model=CustomerSearchLLM,
                max_retries=2,
                context=context,
                tools=[
                    
                ]
            )
        
        return CustomerSearch.from_llm_response(response)
        
    except Exception as e:
        logger.error("Error searching customer information: %s", str(e))
        if isinstance(e, ValidationError):
            raise LLMValidationError(
                message="Failed to validate LLM response",
                validation_error=e,
                details={"customer_id": customer.researcher_id.orcid if isinstance(customer, CustomerProfile) else customer or "unknown"}
            ) from e
        raise LLMAPIError(
            message="Failed to search customer information",
            provider="openai",
            details={"error": str(e), "customer_id": customer.researcher_id.orcid if isinstance(customer, CustomerProfile) else customer or "unknown"}
        ) from e