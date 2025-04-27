from typing import List, Dict, Optional
import logging
import requests
from datetime import datetime
import json

from orcid2taxid.core.models.customer import GrantMetadata
from orcid2taxid.core.utils.date import parse_date
from orcid2taxid.core.logging import get_logger

class NSFRepository:
    """
    Repository implementation for NSF Grants API.
    Uses the NSF Grants API to search for funding information.
    """
    
    def __init__(self, base_url: str = "https://api.nsf.gov/services/v1/awards"):
        """
        Initialize the NSF Grants repository.
        :param base_url: Base URL for the NSF Grants API.
        """
        self.base_url = base_url
        self.headers = {
            'Accept': 'application/json'
        }
        self.logger = get_logger('nsf_grants')

    def _log_error(self, message: str, exc_info: bool = True) -> None:
        """Log an error"""
        self.logger.error(message, exc_info=exc_info)

    def _log_warning(self, message: str) -> None:
        """Log a warning"""
        self.logger.warning(message)

    def _pi_name_matches(self, pi_name: str, search_query: str) -> bool:
        """
        Check if a PI name contains all words from the search query.
        :param pi_name: The PI name to check
        :param search_query: The search query containing words to match
        :return: True if all words from search_query are found in pi_name
        """
        # Convert both strings to lowercase for case-insensitive matching
        pi_name_lower = pi_name.lower()
        search_words = search_query.lower().split()
        
        # Check if all words from the search query are in the PI name
        return all(word in pi_name_lower for word in search_words)

    def _convert_to_grant_metadata(self, nsf_result: Dict) -> GrantMetadata:
        """Helper method to convert NSF result to GrantMetadata"""
        try:
            # Extract organization information
            organization = {
                'name': nsf_result.get('awardeeName', ''),
                'city': nsf_result.get('awardeeCity', ''),
                'state': nsf_result.get('awardeeStateCode', ''),
                'country': 'United States',  # NSF grants are US-based
                'department': '',  # Not provided in basic fields
                'zip': nsf_result.get('awardeeZipCode', '')
            }
            
            # Extract PI information
            pi_data = nsf_result.get('piFirstName', '') + ' ' + nsf_result.get('piLastName', '')
            pi_name = pi_data.strip()
            
            # Extract project terms
            project_terms = []
            if nsf_result.get('title'):
                project_terms.append(nsf_result.get('title'))
            if nsf_result.get('abstractText'):
                project_terms.append(nsf_result.get('abstractText'))
            
            # Create GrantMetadata object with all required fields
            return GrantMetadata(
                project_title=nsf_result.get('title', ''),
                project_num=nsf_result.get('id', ''),
                funder='NSF',  # NSF Grants API is specifically for NSF grants
                fiscal_year=None,  # Not provided in basic fields
                award_amount=None,  # Not provided in basic fields
                direct_costs=None,  # NSF doesn't provide direct/indirect costs
                indirect_costs=None,
                project_start_date=parse_date(nsf_result.get('date')),  # Using award date as start date
                project_end_date=None,  # Not provided in basic fields
                organization=organization,
                pi_name=pi_name,
                pi_profile_id='',  # Not provided in basic fields
                abstract_text=nsf_result.get('abstractText', ''),
                project_terms=project_terms,
                funding_mechanism='',  # Not provided in basic fields
                activity_code='',  # Not provided in basic fields
                award_type='',  # Not provided in basic fields
                study_section=None,  # NIH specific
                study_section_code=None,  # NIH specific
                last_updated=None,  # Not provided in basic fields
                is_active=True,  # Default to True since we don't have status
                is_arra=False,  # NIH specific
                covid_response=None,
                # NSF specific fields
                grant_type='',  # Not provided in basic fields
                grant_status='',  # Not provided in basic fields
                grant_currency='USD',  # NSF grants are always in USD
                grant_country='United States',
                grant_department='',  # Not provided in basic fields
                grant_institution=nsf_result.get('awardeeName', '')
            )
        except Exception as e:
            self._log_error(f"Error converting NSF result to GrantMetadata: {str(e)}")
            return None

    def get_funding_by_pi_name(self, pi_name: str, max_results: int = 20) -> List[GrantMetadata]:
        """
        Search NSF Grants by PI name and convert results to GrantMetadata objects.
        Only returns results where the PI name contains all words from the search query.
        :param pi_name: Principal Investigator name.
        :param max_results: Maximum number of results to fetch.
        :return: List of grant metadata.
        """
        try:
            raw_data = self.fetch_funding_by_pi_name(pi_name, max_results)
            if not raw_data:
                return []
            
            results = raw_data.get('response', {}).get('award', [])
            
            # Convert results to GrantMetadata objects and filter by PI name
            grant_list = []
            for result in results:
                # Construct PI name from first and last name
                result_pi_name = f"{result.get('piFirstName', '')} {result.get('piLastName', '')}".strip()
                
                # Only include results where the PI name matches all words from the search query
                if self._pi_name_matches(result_pi_name, pi_name):
                    grant = self._convert_to_grant_metadata(result)
                    if grant:
                        grant_list.append(grant)
            
            return grant_list
            
        except Exception as e:
            self._log_error(f"Error searching NSF Grants by PI name: {str(e)}")
            return []

    def fetch_funding_by_pi_name(self, pi_name: str, max_results: int = 20) -> Dict:
        """
        Fetch raw funding data from NSF Grants API using PI name.
        Uses exact phrase matching by wrapping the search query in quotes.
        :param pi_name: Principal Investigator name.
        :param max_results: Maximum number of results to fetch.
        :return: Raw API response as a dictionary.
        """
        try:
            # Construct the search parameters with minimal required fields
            # Use exact phrase matching by wrapping the search query in quotes
            params = {
                'keyword': f'"{pi_name}"',
                'printFields': 'id,title,awardeeName,awardeeCity,awardeeStateCode,date,piFirstName,piLastName,abstractText',
                'rpp': min(max_results * 3, 100)  # Fetch more results to account for filtering
            }
            
            # Make the request
            response = requests.get(
                f"{self.base_url}.json",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self._log_error(f"Error fetching NSF Grants data: {str(e)}")
            return {}

    def get_funding_by_organization(self, org_name: str, max_results: int = 20) -> List[GrantMetadata]:
        """
        Search NSF Grants by organization name and convert results to GrantMetadata objects.
        :param org_name: Organization name.
        :param max_results: Maximum number of results to fetch.
        :return: List of grant metadata.
        """
        try:
            raw_data = self.fetch_funding_by_organization(org_name, max_results)
            if not raw_data:
                return []
            
            results = raw_data.get('response', {}).get('award', [])
            
            # Convert results to GrantMetadata objects
            grant_list = []
            for result in results:
                grant = self._convert_to_grant_metadata(result)
                if grant:
                    grant_list.append(grant)
            
            return grant_list
            
        except Exception as e:
            self._log_error(f"Error searching NSF Grants by organization: {str(e)}")
            return []

    def fetch_funding_by_organization(self, org_name: str, max_results: int = 20) -> Dict:
        """
        Fetch raw funding data from NSF Grants API using organization name.
        :param org_name: Organization name.
        :param max_results: Maximum number of results to fetch.
        :return: Raw API response as a dictionary.
        """
        try:
            # Construct the search parameters with minimal required fields
            params = {
                'keyword': org_name,
                'printFields': 'id,title,awardeeName,awardeeCity,awardeeStateCode,date,piFirstName,piLastName,abstractText',
                'rpp': min(max_results, 25)  # Results per page, max 25
            }
            
            # Make the request
            response = requests.get(
                f"{self.base_url}.json",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self._log_error(f"Error fetching NSF Grants data: {str(e)}")
            return {}

    def get_grant_by_number(self, project_number: str) -> Optional[GrantMetadata]:
        """
        Get a single grant by its project number from NSF Grants.
        Since NSF API doesn't support direct field filtering, we fetch results and filter in memory.
        :param project_number: The NSF project number to search for.
        :return: GrantMetadata object if found, None otherwise.
        """
        try:
            raw_data = self.fetch_grant_by_number(project_number)
            if not raw_data or not raw_data.get('response', {}).get('award'):
                self._log_warning(f"No grant found for project number: {project_number}")
                return None
            
            # Find the first award that matches the project number
            awards = raw_data['response']['award']
            matching_award = next(
                (award for award in awards if award.get('id', '').strip() == project_number.strip()),
                None
            )
            
            if not matching_award:
                self._log_warning(f"No exact match found for project number: {project_number}")
                return None
            
            return self._convert_to_grant_metadata(matching_award)
            
        except Exception as e:
            self._log_error(f"Error getting grant by project number: {str(e)}")
            return None

    def fetch_grant_by_number(self, project_number: str) -> Dict:
        """
        Fetch raw grant data from NSF Grants API using project number.
        Since NSF API doesn't support direct field filtering, we use the project number as a keyword.
        :param project_number: The NSF project number to search for.
        :return: Raw API response as a dictionary.
        """
        try:
            # Construct the search parameters with minimal required fields
            params = {
                'keyword': project_number,  # Use project number as keyword
                'printFields': 'id,title,awardeeName,awardeeCity,awardeeStateCode,date,piFirstName,piLastName,abstractText',
                'rpp': 25  # Maximum allowed by NSF API
            }
            
            # Make the request
            response = requests.get(
                f"{self.base_url}.json",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self._log_error(f"Error fetching NSF Grants data: {str(e)}")
            return {} 