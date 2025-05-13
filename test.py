# %%
import instructor
from google import genai
from pydantic import BaseModel
from google.genai import types
from dotenv import load_dotenv
import os

class User(BaseModel):
    name: str
    birth_date: str
    search_result: str

load_dotenv()

client = instructor.from_genai(
    client=genai.Client(api_key=os.getenv("GEMINI_API_KEY")),
    mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
)
tools = [
        types.Tool(google_search=types.GoogleSearch()),
    ]
generate_content_config = types.GenerateContentConfig(
    tools=tools,
    response_mime_type="text/plain",
)

# note that client.chat.completions.create will also work
resp = client.chat.completions.create(
    model="gemini-2.5-pro-preview-05-06",
    messages=[
        {
            "role": "user",
            "content": "Find the exact date of birth of Dina Kuznetsova according to wikipedia",
        },
    ],
    response_model=User,
    config={"config": generate_content_config},
)

print(resp)
# %%

# %%
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Configure tools
tools = [
    types.Tool(google_search=types.GoogleSearch()),
]

# Configure generation settings
generate_content_config = types.GenerateContentConfig(
    tools=tools,
    response_mime_type="text/plain",
)

# Create content request
contents = [
    types.Content(
        role="user",
        parts=[
            types.Part.from_text(text="Find the exact date of birth of Dina Kuznetsova according to wikipedia"),
        ],
    ),
]

# Make request to the model
response = client.models.generate_content(
    model="gemini-2.5-pro-preview-05-06",
    contents=contents,
    config=generate_content_config,
)

# Extract structured data from response
result_text = response.text
print("Raw response:", result_text)

# # Simple parsing example (more robust parsing would be needed for production)
# try:
#     # Attempt to extract JSON-like structure if present
#     if "{" in result_text and "}" in result_text:
#         start_idx = result_text.find("{")
#         end_idx = result_text.rfind("}") + 1
#         json_str = result_text[start_idx:end_idx]
#         user_data = json.loads(json_str)
#         print(f"Name: {user_data.get('name')}, Age: {user_data.get('age')}")
#     else:
#         print("Structured data not found in response")
# except Exception as e:
#     print(f"Error parsing response: {e}")
# %%
