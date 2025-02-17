from typing import List
from schemas.schemas import OrganismMention

class GnfFinder:
    """
    Integrates with the Global Names Finder (GNF) API to detect scientific names
    from an article's text or PDF.
    """
    def __init__(self, gnf_api_url: str):
        """
        :param gnf_api_url: URL for the GNF API endpoint.
        """
        self.gnf_api_url = gnf_api_url

    def find_names_in_text(self, text: str) -> List[OrganismMention]:
        """
        Sends text to GNF for name detection.
        :param text: Article text or abstract.
        :return: List of detected names or codes.
        """
        pass

    def find_names_in_file(self, file_path: str) -> List[OrganismMention]:
        """
        Uploads a file (PDF, text) to the GNF API for name detection.
        :param file_path: File path to the article or other textual resource.
        :return: List of detected names or codes.
        """
        pass 