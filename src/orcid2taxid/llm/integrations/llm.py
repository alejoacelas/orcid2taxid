import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from google import genai
import logging
from aiolimiter import AsyncLimiter

# Set up logging
logger = logging.getLogger(__name__)

def extract_tagged_content(text: str, tag: str) -> Optional[str]:
    """Extract content between XML-like tags.
    
    Args:
        text: The text to extract from
        tag: The tag name without brackets
        
    Returns:
        The content between tags, or None if not found
    """
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    
    start_idx = text.find(start_tag)
    if start_idx == -1:
        return None
        
    start_idx += len(start_tag)
    end_idx = text.find(end_tag, start_idx)
    
    if end_idx == -1:
        return None
        
    return text[start_idx:end_idx].strip()

class LLMClient:
    """Client for interacting with LLMs."""
    
    # Class-level rate limiter for all instances - 3 requests per minute (one every 20 seconds)
    _rate_limiter = AsyncLimiter(100, 60)
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize an LLM client.
        
        Args:
            model: The model name to use for requests
        """
        load_dotenv()
        self.model = model
        self.async_client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

    async def call_async(self, prompt: str) -> str:
        """
        Make an asynchronous call to the LLM.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in the response
            
        Returns:
            The generated text
        """
        # Apply rate limiting
        async with self._rate_limiter:
            response = await self.async_client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
            
    def call(self, prompt: str) -> str:
        """
        Make a synchronous call to the LLM.
        This is a thin wrapper around call_async that creates and runs an event loop.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in the response
            
        Returns:
            The generated text
        """
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the async call
            return loop.run_until_complete(self.call_async(prompt, max_tokens))
        finally:
            loop.close()