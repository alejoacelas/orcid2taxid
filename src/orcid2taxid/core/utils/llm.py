import os
from typing import Optional
from dotenv import load_dotenv
import anthropic
import logging

# Set up logging
logger = logging.getLogger(__name__)

class LLMClient:
    """
    A client for interacting with LLM APIs.
    """
    def __init__(self, model: str = "claude-3-7-sonnet-20250219"):
        """
        Initialize the LLM client.
        
        :param model: Name of the LLM model to be used
        """
        load_dotenv()
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = model

    def call(self, prompt: str, max_tokens: int = 20000, temperature: float = 1) -> str:
        """
        Make a call to the LLM API.
        
        :param prompt: The prompt to send to the LLM
        :param max_tokens: Maximum number of tokens to generate
        :param temperature: Temperature parameter for generation
        :return: The LLM's response text
        """
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
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
        
        return message.content[0].text

def extract_tagged_content(text: str, tag: str) -> Optional[str]:
    """
    Extract content between XML-like tags from text.
    
    :param text: The text to search in
    :param tag: The tag to look for (without < >)
    :return: The content between the tags, or None if not found
    """
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    
    if start_tag in text and end_tag in text:
        start_idx = text.find(start_tag) + len(start_tag)
        end_idx = text.find(end_tag)
        return text[start_idx:end_idx].strip()
    return None