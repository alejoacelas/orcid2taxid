from typing import Any, Dict
import yaml
from jinja2 import Environment, FileSystemLoader

def load_yaml_data(file_path: str) -> Dict[str, Any]:
    """
    Load data from a YAML file.
    
    :param file_path: Path to the YAML file
    :return: Parsed YAML data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_prompt_template(template_dir: str) -> Environment:
    """
    Set up a Jinja environment for loading prompt templates.
    
    :param template_dir: Directory containing the templates
    :param template_name: Name of the template file
    :return: Configured Jinja environment
    """
    return Environment(loader=FileSystemLoader(template_dir))

def render_prompt(template_dir: str, template_name: str, **kwargs: Any) -> str:
    """
    Load and render a prompt template with the provided data.
    
    :param template_dir: Directory containing the templates
    :param template_name: Name of the template file
    :param kwargs: Data to be used in template rendering
    :return: Rendered prompt string
    """
    env = load_prompt_template(template_dir)
    template = env.get_template(template_name)
    return template.render(**kwargs) 