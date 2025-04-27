import json
from typing import Dict, Any, Optional
from pathlib import Path

def get_test_data_dir() -> Path:
    """Get the test data directory path."""
    return Path(__file__).parent.parent / "data"

def get_responses_dir(category: str) -> Path:
    """Get the responses directory for a specific category."""
    responses_dir = get_test_data_dir() / category
    responses_dir.mkdir(exist_ok=True)
    return responses_dir

def save_response(category: str, filename: str, data: Dict[str, Any]) -> None:
    """Save API response to a file."""
    file_path = get_responses_dir(category) / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_response(category: str, filename: str) -> Optional[Dict[str, Any]]:
    """Load saved API response from file."""
    file_path = get_responses_dir(category) / filename
    if not file_path.exists():
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_responses(original: Dict[str, Any], new: Dict[str, Any], timestamp_fields: list[str]) -> bool:
    """Compare two API responses, ignoring specified timestamp fields."""
    def clean_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove timestamp fields and sort keys for comparison."""
        if isinstance(data, dict):
            return {
                k: clean_response(v)
                for k, v in data.items()
                if k not in timestamp_fields
            }
        elif isinstance(data, list):
            return [clean_response(item) for item in data]
        return data

    return clean_response(original) == clean_response(new) 