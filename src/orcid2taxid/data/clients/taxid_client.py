import requests
import logging
from typing import Optional, Dict, Union
from urllib.parse import quote
import json
from orcid2taxid.core.models.schemas import NCBITaxonomyInfo

class NCBITaxIDLookup:
    """
    Uses NCBI e-utils to map organism names to their corresponding TAXIDs.
    """
    def __init__(self):
        """
        Initialize the NCBI TaxID lookup client.
        """
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.tool_name = "orcid2taxid"
        self.email = "alejoacelas@gmail.com"  # Should be configured via environment variable
        # Use module-level logger like other classes
        self.logger = logging.getLogger(__name__)

    def fetch_taxid(self, organism_name: str) -> Optional[Dict]:
        """
        Fetches raw taxonomy data from NCBI for a given organism name.
        
        :param organism_name: The name of the organism to search for.
        :return: Raw API response as a dictionary or None if not found.
        """
        if not organism_name:
            return None

        try:
            # First use esearch to get taxonomy IDs
            search_url = f"{self.base_url}/esearch.fcgi"
            
            # Format the search term - don't use quote() as requests will handle URL encoding
            search_term = organism_name.strip()
            
            params = {
                'db': 'taxonomy',
                'term': search_term,
                'retmode': 'json',
                'tool': self.tool_name,
                'email': self.email
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            search_data = response.json()
            self.logger.debug(f"Search response: {search_data}")
            
            # Check if we got any results
            id_list = search_data.get('esearchresult', {}).get('idlist', [])
            if not id_list:
                self.logger.debug(f"No results found for organism: {organism_name}")
                return None
                
            # Get the first (most relevant) taxonomy ID
            taxid = id_list[0]
            
            # Now fetch the full taxonomy record
            fetch_url = f"{self.base_url}/esummary.fcgi"
            params = {
                'db': 'taxonomy',
                'id': taxid,
                'retmode': 'json',
                'tool': self.tool_name,
                'email': self.email
            }
            
            response = requests.get(fetch_url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching NCBI taxonomy data for {organism_name}", exc_info=True)
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing NCBI taxonomy response for {organism_name}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in NCBI taxonomy lookup for {organism_name}", exc_info=True)
            return None

    def get_taxid(self, organism_name: str) -> Optional[NCBITaxonomyInfo]:
        """
        Returns comprehensive taxonomy information for a given organism name via NCBI requests.
        
        :param organism_name: The name of the organism to map.
        :return: NCBITaxonomyInfo object or None if not found.
        """
        try:
            # Get the raw taxonomy data
            tax_data = self.fetch_taxid(organism_name)
            if not tax_data:
                return None
            
            # Extract the taxonomy information from the response
            result = tax_data.get('result', {})
            if not result:
                return None
                
            # Get the first ID from uids list
            uids = result.get('uids', [])
            if not uids:
                return None
                
            # Get the taxonomy record for the first ID
            tax_record = result.get(str(uids[0]), {})
            
            # Create NCBITaxonomyInfo object
            return NCBITaxonomyInfo(
                taxid=int(uids[0]),
                scientific_name=tax_record.get('scientificname', ''),
                rank=tax_record.get('rank'),
                division=tax_record.get('division'),
                common_name=tax_record.get('commonname'),
                lineage=tax_record.get('lineage', '').split('; ') if tax_record.get('lineage') else None,
                synonyms=tax_record.get('synonym', []),
                genetic_code=tax_record.get('gencode'),
                mito_genetic_code=tax_record.get('mitogenome'),
                is_parasite=tax_record.get('parasite', False),
                is_pathogen=tax_record.get('pathogen', False),
                host_taxid=int(tax_record.get('host_taxid')) if tax_record.get('host_taxid') else None,
                host_scientific_name=tax_record.get('host_scientificname')
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting taxonomy info from NCBI response for {organism_name}", exc_info=True)
            return None