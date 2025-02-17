class NCBITaxIDLookup:
    """
    Uses NCBI e-utils to map organism names to their corresponding TAXIDs.
    """
    def __init__(self, local_db_path: str = None):
        """
        :param local_db_path: Path to local taxonomy DB if available.
        """
        pass

    def get_taxid(self, organism_name: str) -> int:
        """
        Returns the TAXID for a given organism name via either local DB or NCBI requests.
        :param organism_name: The name of the organism to map.
        :return: TAXID integer or None if not found.
        """
        pass