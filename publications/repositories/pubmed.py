from base_repository import BasePublicationRepository
from typing import List, Dict

class PubmedFetcher(BasePublicationRepository):
    SUPPORTS_ORCID_SEARCH = True

    def __init__(self, api_key: str = None):
        """
        :param api_key: An NCBI API key for higher request limits (optional).
        """
        self.api_key = api_key

    def search_by_orcid(self, orcid: str, max_results: int = 20) -> List[Dict]:
        """
        Search PubMed by a given ORCID and return relevant papers.
        :param orcid: ORCID ID.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata dictionaries.
        """
        pass

    def search_by_author_metadata(self, author_metadata: Dict, max_results: int = 20) -> List[Dict]:
        """
        Search PubMed by a given author metadata and return relevant papers.
        :param author_metadata: Author metadata dictionary.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata dictionaries.
        """
        pass