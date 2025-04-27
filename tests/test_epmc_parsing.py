import json
from pydantic import ValidationError
from orcid2taxid.core.models.integrations.epmc_schemas import EpmcResponse
import os

# Construct the absolute path to the JSON file
# Assuming the script is run from the workspace root
script_dir = os.path.dirname(os.path.abspath(__file__)) # tests/
data_dir = os.path.join(script_dir, 'data') # tests/data/
json_file_path = os.path.join(data_dir, 'epmc_sample_responses.json') # tests/data/epmc_sample_responses.json

def test_epmc_parsing():
    """Tests parsing of the sample EPMC response JSON."""
    print(f"Attempting to load JSON from: {json_file_path}")
    
    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found at {json_file_path}")
        return

    try:
        with open(json_file_path, 'r') as f:
            raw_data = json.load(f)
        print("JSON file loaded successfully.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return

    try:
        parsed_response = EpmcResponse.model_validate(raw_data)
        print("\nSuccessfully parsed EPMC response!")
        print(f"Version: {parsed_response.version}")
        print(f"Hit Count: {parsed_response.hit_count}")
        if parsed_response.result_list:
             print(f"Number of results parsed: {len(parsed_response.result_list.result)}")
             # Optionally print details of the first result
             if parsed_response.result_list.result:
                 print(f"First result title: {parsed_response.result_list.result[0].title}")
        else:
            print("No result list found in the parsed data.")

    except ValidationError as e:
        print("\nError parsing EPMC response:")
        print(e)
    except Exception as e:
        print(f"\nAn unexpected error occurred during parsing: {e}")

if __name__ == "__main__":
    test_epmc_parsing() 