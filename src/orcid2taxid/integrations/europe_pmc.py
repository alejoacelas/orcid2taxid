from typing import List, Dict
import logging
import time
import requests
from datetime import datetime

from orcid2taxid.core.models.schemas import Author, FundingInfo, PaperMetadata, ResearcherMetadata, GrantMetadata
from orcid2taxid.core.utils.date import parse_date

class EuropePMCRepository:
    """
    Repository implementation for Europe PMC.
    Uses the Europe PMC REST API to search for publications.
    """
    
    def __init__(self, base_url: str = "https://www.ebi.ac.uk/europepmc/webservices/rest"):
        """
        Initialize the EuropePMC repository.
        :param base_url: Base URL for the Europe PMC API.
        """
        self.base_url = base_url

    def _convert_to_paper_metadata(self, epmc_result: Dict) -> PaperMetadata:
        """Helper method to convert Europe PMC result to PaperMetadata"""
        # Parse publication date to datetime object
        pub_date = None
        try:
            if 'firstPublicationDate' in epmc_result:
                pub_date = parse_date(epmc_result['firstPublicationDate'])
        except (ValueError, TypeError):
            pass

        # Extract authors from authorList if available, fallback to authorString
        authors = []
        if 'authorList' in epmc_result and isinstance(epmc_result['authorList'], dict):
            author_list = epmc_result['authorList'].get('author', [])
            for i, author in enumerate(author_list):
                # Get affiliations and extract email if present
                affiliations = []
                email = None
                if 'authorAffiliationDetailsList' in author:
                    aff_list = author['authorAffiliationDetailsList'].get('authorAffiliation', [])
                    for aff in aff_list:
                        if isinstance(aff, dict) and 'affiliation' in aff:
                            aff_text = aff['affiliation']
                            affiliations.append(aff_text)
                            # Try to extract email from affiliation text
                            if '@' in aff_text and not email:
                                import re
                                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', aff_text)
                                if email_match:
                                    email = email_match.group(0)

                # Get all author identifiers
                author_ids = {}
                if 'authorId' in author and isinstance(author['authorId'], dict):
                    id_type = author['authorId'].get('type', '').lower()
                    id_value = author['authorId'].get('value')
                    if id_type and id_value:
                        author_ids[id_type] = id_value

                # Create Author object with enhanced information
                authors.append(Author(
                    full_name=author.get('fullName', ''),
                    given_name=author.get('firstName', ''),
                    family_name=author.get('lastName', ''),
                    affiliations=affiliations,
                    sequence='first' if i == 0 else 'additional',
                    email=email,
                    identifiers=author_ids
                ))
        elif 'authorString' in epmc_result:
            # Fallback to authorString if no detailed author list
            author_strings = epmc_result['authorString'].split(', ')
            for i, author_string in enumerate(author_strings):
                author_string = author_string.rstrip('.')
                authors.append(Author(
                    full_name=author_string,
                    affiliations=[],
                    sequence='first' if i == 0 else 'additional'
                ))

        # Get full text URL if available (taking only the first one)
        full_text_url = None
        if 'fullTextUrlList' in epmc_result:
            url_list = epmc_result['fullTextUrlList'].get('fullTextUrl', [])
            if url_list and isinstance(url_list[0], dict) and 'url' in url_list[0]:
                full_text_url = url_list[0]['url']

        # Extract funding information
        funding_info = []
        if 'grantsList' in epmc_result and isinstance(epmc_result['grantsList'], dict):
            grants = epmc_result['grantsList'].get('grant', [])
            if not isinstance(grants, list):
                grants = [grants]  # Handle case where single grant is returned as dict
            
            for grant in grants:
                if not isinstance(grant, dict):
                    continue
                    
                # Extract organization information safely
                organization = {}
                if grant.get('institution'):
                    organization['name'] = grant['institution']
                if grant.get('department'):
                    organization['department'] = grant['department']
                if grant.get('country'):
                    organization['country'] = grant['country']
                if grant.get('city'):
                    organization['city'] = grant['city']
                if grant.get('state'):
                    organization['state'] = grant['state']
                if grant.get('zip'):
                    organization['zip'] = grant['zip']
                
                # Extract project terms safely
                project_terms = []
                if grant.get('grantTitle'):
                    project_terms.append(grant['grantTitle'])
                if grant.get('grantType'):
                    project_terms.append(grant['grantType'])
                if grant.get('keywords'):
                    if isinstance(grant['keywords'], list):
                        project_terms.extend(grant['keywords'])
                    elif isinstance(grant['keywords'], str):
                        project_terms.append(grant['keywords'])
                
                # Try to extract fiscal year from grant ID if available
                fiscal_year = None
                if grant.get('grantId'):
                    try:
                        # Try to extract year from grant ID (common formats: YYYY-XXXX or YYYY/XXXX)
                        year_str = grant['grantId'].split('-')[0] if '-' in grant['grantId'] else grant['grantId'].split('/')[0]
                        if len(year_str) == 4 and year_str.isdigit():
                            fiscal_year = int(year_str)
                    except (ValueError, IndexError):
                        pass
                
                # Create GrantMetadata object with available information
                grant_metadata = GrantMetadata(
                    project_title=grant.get('grantTitle', ''),
                    project_num=grant.get('grantId', ''),
                    funder=grant.get('agency', ''),
                    fiscal_year=fiscal_year,
                    award_amount=float(grant.get('amount', 0)) if grant.get('amount') else None,
                    direct_costs=None,  # Europe PMC doesn't provide direct/indirect costs
                    indirect_costs=None,
                    project_start_date=parse_date(grant.get('startDate')),
                    project_end_date=parse_date(grant.get('endDate')),
                    organization=organization,
                    pi_name=grant.get('piName', ''),
                    pi_profile_id=grant.get('piId', ''),
                    abstract_text=grant.get('description', ''),
                    project_terms=project_terms,
                    funding_mechanism=grant.get('mechanism', ''),
                    activity_code=None,  # Europe PMC specific
                    award_type=grant.get('grantType', ''),
                    study_section=None,  # NIH specific
                    study_section_code=None,  # NIH specific
                    last_updated=parse_date(grant.get('lastUpdateDate')),
                    is_active=bool(grant.get('isCurrent')),
                    is_arra=False,  # NIH specific
                    covid_response=None,  # NIH specific
                    # Europe PMC specific fields
                    grant_type=grant.get('grantType', ''),
                    grant_status='active' if grant.get('isCurrent') else 'completed',
                    grant_currency=grant.get('currency', ''),
                    grant_country=grant.get('country', ''),
                    grant_department=grant.get('department', ''),
                    grant_institution=grant.get('institution', '')
                )
                funding_info.append(grant_metadata)

        # Ensure keywords is always a list, even if empty
        keywords = []
        keyword_list = epmc_result.get('keywordList', {})
        if isinstance(keyword_list, dict):
            keyword_array = keyword_list.get('keyword', [])
            if isinstance(keyword_array, list):
                keywords = [k for k in keyword_array if isinstance(k, str)]

        # Build PaperMetadata object with enhanced information
        return PaperMetadata(
            title=epmc_result.get('title', ''),
            abstract=epmc_result.get('abstractText', ''),
            doi=epmc_result.get('doi'),
            publication_date=pub_date,
            journal_name=epmc_result.get('journalInfo', {}).get('journal', {}).get('title'),
            journal_issn=epmc_result.get('journalInfo', {}).get('journal', {}).get('issn'),
            authors=authors,
            full_text_url=full_text_url,
            citation_count=epmc_result.get('citedByCount'),
            keywords=keywords,
            subjects=[mesh['descriptorName'] for mesh in epmc_result.get('meshHeadingList', {}).get('meshHeading', []) if isinstance(mesh, dict) and 'descriptorName' in mesh],
            funding_info=funding_info
        )

    def get_publications_by_orcid(self, orcid: str, max_results: int = 20) -> List[PaperMetadata]:
        """
        Search Europe PMC by ORCID ID and convert results to PaperMetadata objects.
        :param orcid: ORCID ID.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata.
        """
        try:
            raw_data = self.fetch_publications_by_orcid(orcid, max_results)
            if not raw_data:
                return []
            
            results = raw_data.get('resultList', {}).get('result', [])
            
            # Convert results to PaperMetadata objects
            papers = []
            for result in results:
                papers.append(self._convert_to_paper_metadata(result))
                time.sleep(0.1)  # Be nice to the API
                
            return papers
            
        except Exception as e:
            logging.error("Error searching Europe PMC by ORCID", exc_info=True)
            return []

    def get_publications_by_researcher_metadata(self, researcher_metadata: Dict, max_results: int = 20) -> List[PaperMetadata]:
        """
        Search Europe PMC by researcher metadata and convert results to PaperMetadata objects.
        :param researcher_metadata: Researcher metadata dictionary.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata.
        """
        try:
            raw_data = self.fetch_publications_by_researcher_metadata(researcher_metadata, max_results)
            if not raw_data:
                return []
            
            results = raw_data.get('resultList', {}).get('result', [])
            
            # Convert results to PaperMetadata objects
            papers = []
            for result in results:
                papers.append(self._convert_to_paper_metadata(result))
                time.sleep(0.1)  # Be nice to the API
                
            return papers
            
        except Exception as e:
            logging.error("Error searching Europe PMC by researcher metadata", exc_info=True)
            return []

    def fetch_publications_by_orcid(self, orcid: str, max_results: int = 20) -> Dict:
        """
        Fetch raw publication data from Europe PMC API using ORCID ID.
        :param orcid: ORCID ID.
        :param max_results: Maximum number of results to fetch.
        :return: Raw API response as a dictionary.
        """
        try:
            # Construct the search URL
            search_url = f"{self.base_url}/search"
            params = {
                'query': f'AUTHORID:"{orcid}"',
                'format': 'json',
                'pageSize': max_results,
                'resultType': 'core'  # Get full results instead of lite
            }
            
            # Make the request
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception:
            logging.error("Error fetching Europe PMC publications by ORCID", exc_info=True)
            return {}

    def fetch_publications_by_researcher_metadata(self, researcher_metadata: Dict, max_results: int = 20) -> Dict:
        """
        Fetch raw publication data from Europe PMC API using researcher metadata.
        :param researcher_metadata: Researcher metadata dictionary or ResearcherMetadata object.
        :param max_results: Maximum number of results to fetch.
        :return: Raw API response as a dictionary.
        """
        try:
            # Convert AuthorMetadata object to dict if needed
            if isinstance(researcher_metadata, ResearcherMetadata):
                researcher_metadata = researcher_metadata.model_dump()
            
            query_parts = []
            
            # Add author name in Europe PMC format
            if researcher_metadata.get('family_name') and researcher_metadata.get('given_name'):
                # Construct name from parts in the format "Segireddy Rameswara Reddy"
                author_name = f"{researcher_metadata['family_name']} {researcher_metadata['given_name']}"
                author_name = author_name.replace(',', '').strip()
                query_parts.append(f'AUTH:"{author_name}"')
            elif researcher_metadata.get('full_name'):
                # Try to parse from full_name, assuming format "Lastname, Firstname"
                full_name = researcher_metadata['full_name']
                # Split on comma and reverse to get "Lastname Firstname" format
                name_parts = [part.strip() for part in full_name.split(',')]
                if len(name_parts) == 2:
                    author_name = f"{name_parts[0]} {name_parts[1]}"
                else:
                    author_name = full_name.replace(',', '').strip()
                query_parts.append(f'AUTH:"{author_name}"')

            if not query_parts:
                return {}

            # Add ORCID if available
            if researcher_metadata.get('orcid'):
                query_parts.append(f'AUTHORID:"{researcher_metadata["orcid"]}"')

            # Combine query parts with OR to be more permissive
            query = " OR ".join(query_parts)
            
            # Construct the search URL
            search_url = f"{self.base_url}/search"
            params = {
                'query': query,
                'format': 'json',
                'pageSize': max_results,
                'resultType': 'core'  # Get full results instead of lite
            }
            
            # Make the request
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception:
            logging.error(f"Error fetching Europe PMC publications by author metadata", exc_info=True)
            return {}
