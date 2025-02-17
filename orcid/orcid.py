class OrcidFetcher:
    """
    Responsible for querying the ORCID API to retrieve researcher
    metadata and publications using an ORCID ID.
    """
    def __init__(self, api_key: str = None):
        """
        :param api_key: (Optional) API key if needed for ORCID's advanced endpoints.
        """
        pass

    def fetch_researcher_info(self, orcid_id: str) -> dict:
        """
        Fetches a researcher's metadata (e.g., name, institution).
        :param orcid_id: ORCID ID (string).
        :return: Dictionary containing researcher info.
        """
        pass

    def fetch_publications(self, orcid_id: str) -> list:
        """
        Fetches a list of publications for the given ORCID ID.
        :param orcid_id: ORCID ID.
        :return: List of publication data (JSON-like).
        """
        pass 