from base_repository import BasePublicationRepository
from typing import List, Dict

class BiorxivFetcher(BasePublicationRepository):
    SUPPORTS_ORCID_SEARCH = False

    def __init__(self, base_url: str = "https://api.biorxiv.org/"):
        """
        :param base_url: Base URL for biorxiv API endpoints.
        """
        self.base_url = base_url

    def search_by_orcid(self, orcid: str, max_results: int = 20) -> List[Dict]:
        """
        Search biorxiv/medRxiv by a given ORCID and return relevant papers.
        Note: This method won't be called since SUPPORTS_ORCID_SEARCH is False.
        
        :param orcid: ORCID ID.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata dictionaries.
        """
        raise NotImplementedError("bioRxiv does not support direct ORCID search")

    def search_by_author_metadata(self, author_metadata: Dict, max_results: int = 20) -> List[Dict]:
        """
        Search biorxiv/medRxiv by a given author metadata and return relevant papers.
        :param author_metadata: Author metadata dictionary.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata dictionaries.
        """
        pass