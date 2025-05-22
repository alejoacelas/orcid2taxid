import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types

@dataclass
class Message:
    content: str
    role: str

@dataclass
class Choice:
    message: Message
    index: int
    logprobs: Optional[Any] = None
    finish_reason: Optional[str] = None

@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class Response:
    id: Optional[str]
    object: str
    created: Optional[int]
    model: str
    system_fingerprint: Optional[str]
    choices: List[Choice]
    usage: Usage
    gemini_metadata: Dict[str, Any]

def gemini_create_with_search(*, messages, model, tools=None, **_kwargs):
    """
    Accepts the same signature Instructor/OpenAI use and forwards
    it to Gemini with Google Search enabled by default, then adapts the response shape back.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Convert OpenAI-style messages → Gemini Contents
    role_map = {"system": "user", "user": "user", "assistant": "model"}
    contents = [
        types.Content(
            role=role_map.get(m["role"], "user"),
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in messages
    ]

    # Always include Google Search tool
    search_tool = types.Tool(google_search=types.GoogleSearch())
    tools = [search_tool] + (tools or [])

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            tools=tools,
            response_mime_type="text/plain",
        ),
    )

    # Extract text from Gemini response
    text = response.candidates[0].content.parts[0].text
    
    # Create usage object
    usage = Usage(
        prompt_tokens=response.usage_metadata.prompt_token_count,
        completion_tokens=response.usage_metadata.candidates_token_count,
        total_tokens=response.usage_metadata.total_token_count
    )
    
    # Create choice object with message
    choice = Choice(
        message=Message(content=text, role="assistant"),
        index=response.candidates[0].index,
        logprobs=None,
        finish_reason=response.candidates[0].finish_reason
    )
    
    # Gemini-specific information
    grounding_metadata = response.candidates[0].grounding_metadata if response.candidates[0].grounding_metadata else None
    gemini_metadata = {
        "grounding": {
            "queries": grounding_metadata.web_search_queries if grounding_metadata else None,
            "sources": [
                {
                    "title": chunk.web.title if chunk.web else None,
                    "uri": chunk.web.uri if chunk.web else None
                }
                for chunk in (grounding_metadata.grounding_chunks if grounding_metadata and grounding_metadata.grounding_chunks else [])
            ]
        }
    }
    
    # Create and return response object
    return Response(
        id=None,  # Gemini doesn't provide this
        object="text_completion",
        created=None,  # Gemini doesn't provide this
        model=response.model_version,
        system_fingerprint=None,  # Gemini doesn't provide this
        choices=[choice],
        usage=usage,
        gemini_metadata=gemini_metadata
    )
