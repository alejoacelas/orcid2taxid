from typing import List, Dict
from orcid2taxid.core.models.schemas import PaperMetadata, Author, ExternalId, FundingInfo, AuthorMetadata
import requests
import time
import logging
from orcid2taxid.core.utils.date import parse_date_to_iso

class EuropePMCRepository:
    """
    Repository implementation for Europe PMC.
    Uses the Europe PMC REST API to search for publications.
    """
    SUPPORTS_ORCID_SEARCH = True
    
    def __init__(self, base_url: str = "https://www.ebi.ac.uk/europepmc/webservices/rest"):
        """
        Initialize the EuropePMC repository.
        :param base_url: Base URL for the Europe PMC API.
        """
        self.base_url = base_url

    def _convert_to_paper_metadata(self, epmc_result: Dict) -> PaperMetadata:
        """Helper method to convert Europe PMC result to PaperMetadata"""
        # Parse publication date to ISO format string
        pub_date = None
        try:
            if 'firstPublicationDate' in epmc_result:
                pub_date = parse_date_to_iso(epmc_result['firstPublicationDate'])
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
                        if id_type == 'orcid':
                            orcid = id_value

                # Create Author object with enhanced information
                authors.append(Author(
                    full_name=author.get('fullName', ''),
                    given_name=author.get('firstName', ''),
                    family_name=author.get('lastName', ''),
                    affiliations=affiliations,
                    sequence='first' if i == 0 else 'additional',
                    orcid=orcid if 'orcid' in locals() else None,
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

        # Extract external identifiers including full text IDs
        external_ids = {}
        if epmc_result.get('doi'):
            external_ids['doi'] = ExternalId(
                value=epmc_result['doi'],
                url=f"https://doi.org/{epmc_result['doi']}"
            )
        if epmc_result.get('pmid'):
            external_ids['pmid'] = ExternalId(
                value=epmc_result['pmid'],
                url=f"https://pubmed.ncbi.nlm.nih.gov/{epmc_result['pmid']}"
            )
        if epmc_result.get('pmcid'):
            external_ids['pmcid'] = ExternalId(
                value=epmc_result['pmcid'],
                url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{epmc_result['pmcid']}"
            )
        
        # Get full text URLs if available
        full_text_urls = []
        if 'fullTextUrlList' in epmc_result:
            url_list = epmc_result['fullTextUrlList'].get('fullTextUrl', [])
            for url_info in url_list:
                if isinstance(url_info, dict) and 'url' in url_info:
                    full_text_urls.append(url_info['url'])

        # Extract detailed journal information
        journal_info = {}
        if 'journalInfo' in epmc_result and isinstance(epmc_result['journalInfo'], dict):
            journal = epmc_result['journalInfo'].get('journal', {})
            if isinstance(journal, dict):
                journal_info = {
                    'title': journal.get('title'),
                    'issn': journal.get('issn'),
                    'eissn': journal.get('essn'),
                    'nlm_id': journal.get('nlmid'),
                    'iso_abbreviation': journal.get('isoabbreviation'),
                    'volume': epmc_result['journalInfo'].get('volume'),
                    'issue': epmc_result['journalInfo'].get('issue')
                }

        # Extract funding information
        funding_info = []
        if 'grantsList' in epmc_result:
            for grant in epmc_result['grantsList'].get('grant', []):
                if isinstance(grant, dict):
                    funding_info.append(FundingInfo(
                        name=grant.get('grantTitle'),
                        grant_number=grant.get('grantId'),
                        funder=grant.get('agency')
                    ))

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
            doi=epmc_result.get('doi'),
            pmid=epmc_result.get('pmid'),
            publication_date=pub_date,
            journal=journal_info.get('title'),
            journal_info=journal_info,
            abstract=epmc_result.get('abstractText', ''),
            authors=authors,
            repository_source='europepmc',
            type=epmc_result.get('pubType', [None])[0] if isinstance(epmc_result.get('pubType'), list) else epmc_result.get('pubType', ''),
            url=full_text_urls[0] if full_text_urls else None,
            full_text_urls=full_text_urls,
            citation_count=epmc_result.get('citedByCount'),
            keywords=keywords,
            subjects=[mesh['descriptorName'] for mesh in epmc_result.get('meshHeadingList', {}).get('meshHeading', []) if isinstance(mesh, dict) and 'descriptorName' in mesh],
            funding_info=funding_info if 'funding_info' in locals() else None,
            external_ids=external_ids,
            language=epmc_result.get('language'),
            publication_status=epmc_result.get('publicationStatus'),
            is_open_access=epmc_result.get('isOpenAccess') == 'Y',
            has_pdf=epmc_result.get('hasPDF') == 'Y',
            country=None,
            visibility='public'
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

    def get_publications_by_author_metadata(self, author_metadata: Dict, max_results: int = 20) -> List[PaperMetadata]:
        """
        Search Europe PMC by author metadata and convert results to PaperMetadata objects.
        :param author_metadata: Author metadata dictionary.
        :param max_results: Maximum number of results to fetch.
        :return: List of publication metadata.
        """
        try:
            raw_data = self.fetch_publications_by_author_metadata(author_metadata, max_results)
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
            logging.error("Error searching Europe PMC by author metadata", exc_info=True)
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

    def fetch_publications_by_author_metadata(self, author_metadata: Dict, max_results: int = 20) -> Dict:
        """
        Fetch raw publication data from Europe PMC API using author metadata.
        :param author_metadata: Author metadata dictionary or AuthorMetadata object.
        :param max_results: Maximum number of results to fetch.
        :return: Raw API response as a dictionary.
        """
        try:
            # Convert AuthorMetadata object to dict if needed
            if isinstance(author_metadata, AuthorMetadata):
                author_metadata = author_metadata.model_dump()
            
            query_parts = []
            
            # Add author name in Europe PMC format
            if author_metadata.get('family_name') and author_metadata.get('given_name'):
                # Construct name from parts in the format "Segireddy Rameswara Reddy"
                author_name = f"{author_metadata['family_name']} {author_metadata['given_name']}"
                author_name = author_name.replace(',', '').strip()
                query_parts.append(f'AUTH:"{author_name}"')
            elif author_metadata.get('full_name'):
                # Try to parse from full_name, assuming format "Lastname, Firstname"
                full_name = author_metadata['full_name']
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
            if author_metadata.get('orcid'):
                query_parts.append(f'AUTHORID:"{author_metadata["orcid"]}"')

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
