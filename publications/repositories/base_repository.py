from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from schemas.schemas import PaperMetadata, AuthorMetadata

class BasePublicationRepository(ABC):
    """
    Abstract base class for publication repositories.
    Defines common interface for searching publications across different sources.
    """
    
    SUPPORTS_ORCID_SEARCH: bool = False

    @abstractmethod
    def search_by_orcid(self, orcid: str, max_results: int = 20) -> List[PaperMetadata]:
        """
        Search repository by ORCID ID.
        :param orcid: ORCID ID.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata dictionaries.
        """
        pass

    @abstractmethod
    def search_by_author_metadata(self, author_metadata: AuthorMetadata, max_results: int = 20) -> List[PaperMetadata]:
        """
        Search repository by author metadata.
        :param author_metadata: Author metadata dictionary.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata dictionaries.
        """
        pass

    def search_publications(self, orcid: str, author_metadata: AuthorMetadata, max_results: int = 20) -> List[PaperMetadata]:
        """
        Smart search that uses the most appropriate search method based on repository capabilities.
        
        :param orcid: ORCID ID.
        :param author_metadata: Author metadata dictionary.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata dictionaries.
        """
        if self.SUPPORTS_ORCID_SEARCH:
            return self.search_by_orcid(orcid, max_results)
        return self.search_by_author_metadata(author_metadata, max_results)