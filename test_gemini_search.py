# %%
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from orcid2taxid.llm.utils.instructor import load_instructor_client

# Load environment variables
load_dotenv()

# Define a simple schema for the response
class Biography(BaseModel):
    biography: str = Field(..., description="The biography information found from Technology Networks")
    source_url: str = Field(..., description="The Technology Networks URL where the biography was found")

def test_gemini_search():
    # Initialize the instructor client with Gemini and search enabled
    client = load_instructor_client(
        model="gemini-2.5-pro-preview-05-06",
        use_search=True
    )
    
    # Create a simple prompt to search for a specific fact
    prompt = """
    Find the biography of Jean Peccoud profiled at Technology Networks.
    Provide the biography information and the Technology Networks URL where you found this information.
    """
    
    # Make the request using instructor
    response = client.chat.completions.create(
        model="gemini-2.5-pro-preview-05-06",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        response_model=Biography,
        max_retries=2
    )
    
    # Print the result
    print("\nSearch Result:")
    print(f"Biography: {response.biography}")
    print(f"Source: {response.source_url}")

if __name__ == "__main__":
    test_gemini_search() 
# %%
