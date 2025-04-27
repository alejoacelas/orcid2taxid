from orcid2taxid.core.logging import get_logger

logger = get_logger(__name__)

class UnpaywallFetcher:
    """
    Uses the Unpaywall API to download a publication's PDF when available for a given DOI.
    """

    def __init__(self, email: str):
        """
        :param email: Email address required by Unpaywall's usage policy.
        """

    def fetch_fulltext_link(self, doi: str) -> dict:
        """
        Lookup the given DOI in Unpaywall to see if there's a free PDF or HTML version.
        :param doi: The paper's DOI.
        :return: A dictionary with info on the OA status, link to PDF/HTML, etc.
        """

    def download_pdf(self, doi: str, save_path: str) -> bool:
        """
        If a free PDF link exists, download it to the specified path.
        :param doi: Paper's DOI.
        :param save_path: Where to store the downloaded PDF locally.
        :return: True if download succeeded, False otherwise.
        """ 