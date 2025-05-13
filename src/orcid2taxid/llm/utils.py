from pathlib import Path
import os
from dotenv import load_dotenv
import instructor
from openai import OpenAI
from orcid2taxid.core.logging import get_logger
from google import genai
from anthropic import Anthropic

logger = get_logger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"

# Mapping of model names to their providers and corresponding API key environment variables
MODEL_PROVIDERS = {
    "claude-3-7-sonnet": "ANTHROPIC",
    "o3": "OPENAI",
    "o3-mini": "OPENAI",
    "gpt-4o": "OPENAI",
    "gemini-2.0-flash": "GEMINI",
    "gemini-2.5-pro-preview-05-06": "GEMINI",
}

def load_instructor_client(model: str = "gemini-2.0-flash") -> instructor.Instructor:
    """
    Initialize and return an Instructor client configured for the specified model.
    
    :param model: The model name to use (default: gemini-2.0-flash)
    :return: Configured Instructor client
    :raises: ValueError if model is not supported or API key is not set
    """
    load_dotenv()
    
    if model not in MODEL_PROVIDERS:
        raise ValueError(f"Unsupported model: {model}.\nSupported models: {list(MODEL_PROVIDERS.keys())}")
    provider = MODEL_PROVIDERS[model]
    
    api_key = os.getenv(f"{provider}_API_KEY")
    if not api_key:
        raise ValueError(f"{provider} API key environment variable not set")
    
    # Initialize appropriate client based on provider
    if provider == "OPENAI":
        client = instructor.from_openai(OpenAI(api_key=api_key))
    elif provider == "ANTHROPIC":
        client = instructor.from_anthropic(Anthropic(api_key=api_key))
    elif provider == "GEMINI":
        client = instructor.from_genai(genai.Client(api_key=api_key))
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return client

def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    :param prompt_name: Name of the prompt file (e.g., 'abstract_only_organism_extraction.txt')
    :return: Contents of the prompt file
    :raises: FileNotFoundError if prompt file doesn't exist
    """
    prompt_path = PROMPT_DIR / prompt_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_name}")
    
    return prompt_path.read_text()
