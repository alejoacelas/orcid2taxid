from typing import List, Dict, Optional
import logging
import requests
from datetime import datetime
import json

from orcid2taxid.core.models.customer import GrantMetadata
from orcid2taxid.core.utils.date import parse_date
from orcid2taxid.core.config.logging import get_logger

class NIHReporterRepository:
    """
    Repository implementation for NIH Reporter.
    Uses the NIH Reporter API to search for funding information.
    """
    
    def __init__(self, base_url: str = "https://api.reporter.nih.gov/v2"):
        """
        Initialize the NIH Reporter repository.
        :param base_url: Base URL for the NIH Reporter API.
        """
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.logger = get_logger('nih_reporter')

    def _log_error(self, message: str, exc_info: bool = True) -> None:
        """Log an error"""
        self.logger.error(message, exc_info=exc_info)

    def _log_warning(self, message: str) -> None:
        """Log a warning"""
        self.logger.warning(message)

    def _convert_to_grant_metadata(self, nih_result: Dict) -> GrantMetadata:
        """Helper method to convert NIH Reporter result to GrantMetadata"""
        try:
            # Extract organization information
            org_data = nih_result.get('organization', {})
            # Handle DUNS number which comes as a list
            duns = org_data.get('org_duns', [])
            duns_str = duns[0] if isinstance(duns, list) and duns else ''
            
            organization = {
                'name': org_data.get('org_name', ''),
                'city': org_data.get('org_city', ''),
                'state': org_data.get('org_state', ''),
                'country': org_data.get('org_country', ''),
                'department': org_data.get('org_dept', ''),
                'duns': duns_str,
                'zip': org_data.get('org_zip', '')
            }
            
            # Extract PI information
            pi_data = nih_result.get('contact_pi', {})
            pi_name = f"{pi_data.get('last_name', '')}, {pi_data.get('first_name', '')}".strip(', ')
            
            # Extract project terms
            project_terms = []
            terms_data = nih_result.get('project_terms', {})
            if isinstance(terms_data, dict):
                for term in terms_data.get('term', []):
                    if isinstance(term, dict) and term.get('term'):
                        project_terms.append(term['term'])
            
            # Create GrantMetadata object with all required fields
            return GrantMetadata(
                project_title=nih_result.get('project_title', ''),
                project_num=nih_result.get('project_num', ''),
                funder='NIH',  # NIH Reporter is specifically for NIH grants
                fiscal_year=nih_result.get('fiscal_year'),
                award_amount=float(nih_result.get('award_amount', 0)) if nih_result.get('award_amount') else None,
                direct_costs=float(nih_result.get('direct_cost_amt', 0)) if nih_result.get('direct_cost_amt') else None,
                indirect_costs=float(nih_result.get('indirect_cost_amt', 0)) if nih_result.get('indirect_cost_amt') else None,
                project_start_date=parse_date(nih_result.get('project_start_date')),
                project_end_date=parse_date(nih_result.get('project_end_date')),
                organization=organization,
                pi_name=pi_name,
                pi_profile_id=pi_data.get('profile_id'),
                abstract_text=nih_result.get('abstract_text'),
                project_terms=project_terms,
                funding_mechanism=nih_result.get('funding_mechanism'),
                activity_code=nih_result.get('activity_code'),
                award_type=nih_result.get('award_type'),
                study_section=nih_result.get('study_section'),
                study_section_code=nih_result.get('study_section_code'),
                last_updated=parse_date(nih_result.get('last_update_date')),
                is_active=nih_result.get('is_active', False),
                is_arra=nih_result.get('arra_funded', False),
                covid_response=nih_result.get('covid_response'),
                # Add required fields with appropriate values
                grant_type=nih_result.get('award_type', 'research'),  # Default to research if not specified
                grant_status='active' if nih_result.get('is_active', False) else 'completed',
                grant_currency='USD',  # NIH grants are always in USD
                grant_country=org_data.get('org_country', 'United States'),
                grant_department=org_data.get('org_dept', ''),
                grant_institution=org_data.get('org_name', '')
            )
        except Exception as e:
            self._log_error(f"Error converting NIH Reporter result to GrantMetadata: {str(e)}")
            return None

    def get_funding_by_pi_name(self, pi_name: str, max_results: int = 20) -> List[GrantMetadata]:
        """
        Search NIH Reporter by PI name and convert results to GrantMetadata objects.
        :param pi_name: Principal Investigator name.
        :param max_results: Maximum number of results to fetch.
        :return: List of grant metadata.
        """
        try:
            raw_data = self.fetch_funding_by_pi_name(pi_name, max_results)
            if not raw_data:
                return []
            
            results = raw_data.get('results', [])
            
            # Convert results to GrantMetadata objects
            grant_list = []
            for result in results:
                grant = self._convert_to_grant_metadata(result)
                if grant:
                    grant_list.append(grant)
            
            return grant_list
            
        except Exception as e:
            self._log_error(f"Error searching NIH Reporter by PI name: {str(e)}")
            return []

    def fetch_funding_by_pi_name(self, pi_name: str, max_results: int = 20) -> Dict:
        """
        Fetch raw funding data from NIH Reporter API using PI name.
        :param pi_name: Principal Investigator name.
        :param max_results: Maximum number of results to fetch.
        :return: Raw API response as a dictionary.
        """
        try:
            # Construct the search URL
            search_url = f"{self.base_url}/projects/search"
            
            # Construct the search criteria
            search_criteria = {
                "criteria": {
                    "pi_names": [{"any": pi_name}],
                    "advanced_text_search": {
                        "operator": "AND",
                        "search_field": "all",
                        "search_text": pi_name
                    }
                },
                "limit": max_results,
                "offset": 0,
                "sort_field": "project_start_date",
                "sort_order": "desc"
            }
            
            # Make the request
            response = requests.post(
                search_url,
                headers=self.headers,
                json=search_criteria
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self._log_error(f"Error fetching NIH Reporter funding data: {str(e)}")
            return {}

    def get_funding_by_organization(self, org_name: str, max_results: int = 20) -> List[GrantMetadata]:
        """
        Search NIH Reporter by organization name and convert results to GrantMetadata objects.
        :param org_name: Organization name.
        :param max_results: Maximum number of results to fetch.
        :return: List of grant metadata.
        """
        try:
            raw_data = self.fetch_funding_by_organization(org_name, max_results)
            if not raw_data:
                return []
            
            results = raw_data.get('results', [])
            
            # Convert results to GrantMetadata objects
            grant_list = []
            for result in results:
                grant = self._convert_to_grant_metadata(result)
                if grant:
                    grant_list.append(grant)
            
            return grant_list
            
        except Exception as e:
            self._log_error(f"Error searching NIH Reporter by organization: {str(e)}")
            return []

    def fetch_funding_by_organization(self, org_name: str, max_results: int = 20) -> Dict:
        """
        Fetch raw funding data from NIH Reporter API using organization name.
        :param org_name: Organization name.
        :param max_results: Maximum number of results to fetch.
        :return: Raw API response as a dictionary.
        """
        try:
            # Construct the search URL
            search_url = f"{self.base_url}/projects/search"
            
            # Construct the search criteria
            search_criteria = {
                "criteria": {
                    "organization_names": [{"any": org_name}],
                    "advanced_text_search": {
                        "operator": "AND",
                        "search_field": "all",
                        "search_text": org_name
                    }
                },
                "limit": max_results,
                "offset": 0,
                "sort_field": "project_start_date",
                "sort_order": "desc"
            }
            
            # Make the request
            response = requests.post(
                search_url,
                headers=self.headers,
                json=search_criteria
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self._log_error(f"Error fetching NIH Reporter funding data: {str(e)}")
            return {}

    def get_grant_by_number(self, project_number: str) -> Optional[GrantMetadata]:
        """
        Get a single grant by its project number from NIH Reporter.
        :param project_number: The NIH project number to search for.
        :return: GrantMetadata object if found, None otherwise.
        """
        try:
            raw_data = self.fetch_grant_by_number(project_number)
            if not raw_data or not raw_data.get('results'):
                self._log_warning(f"No grant found for project number: {project_number}")
                return None
            
            # Get the first result and convert it to GrantMetadata
            result = raw_data['results'][0]
            return self._convert_to_grant_metadata(result)
            
        except Exception as e:
            self._log_error(f"Error getting grant by project number: {str(e)}")
            return None

    def fetch_grant_by_number(self, project_number: str) -> Dict:
        """
        Fetch raw grant data from NIH Reporter API using project number.
        :param project_number: The NIH project number to search for.
        :return: Raw API response as a dictionary.
        """
        try:
            # Construct the search URL
            search_url = f"{self.base_url}/projects/search"
            
            # Construct the search criteria
            search_criteria = {
                "criteria": {
                    "project_nums": [project_number]
                },
                "limit": 1,  # We only need one result
                "offset": 0
            }
            
            # Make the request
            response = requests.post(
                search_url,
                headers=self.headers,
                json=search_criteria
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self._log_error(f"Error fetching NIH Reporter grant data: {str(e)}")
            return {}
