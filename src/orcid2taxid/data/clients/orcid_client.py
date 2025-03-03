import requests
import json
import logging
from orcid2taxid.core.models.schemas import (
    AuthorMetadata, 
    AuthorAffiliation, 
    ExternalId, 
    ResearcherUrl, 
    EmailInfo, 
    CountryInfo
)
from datetime import datetime

class OrcidClient:
    """
    Responsible for querying the ORCID API to retrieve researcher
    metadata and publications using an ORCID ID.
    """
    def __init__(self, api_key: str = None):
        """
        :param api_key: (Optional) API key if needed for ORCID's advanced endpoints.
        """
        self.api_key = api_key
        self.base_url = "https://pub.orcid.org/v3.0"
        self.headers = {
            'Accept': 'application/vnd.orcid+json'  # Specify JSON format explicitly
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    def get_author_metadata(self, orcid_id: str) -> AuthorMetadata:
        """
        Fetches a researcher's metadata (e.g., name, institution).
        :param orcid_id: ORCID ID (string).
        :return: AuthorMetadata object containing researcher info.
        """

        try:
            # Make request to ORCID API
            response = requests.get(
                f"{self.base_url}/{orcid_id}/person",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Initialize with required fields
            full_name = None
            name_data = data.get('name', {}) if data else {}
            if name_data:
                given_name = name_data.get('given-names', {})
                family_name = name_data.get('family-name', {})
                given_name_value = given_name.get('value', '') if given_name else ''
                family_name_value = family_name.get('value', '') if family_name else ''
                if given_name_value or family_name_value:
                    full_name = f"{family_name_value}, {given_name_value}".strip(', ')
            
            if not full_name:
                full_name = "Unknown"  # Fallback for required field
            
            researcher_info = {
                'orcid': orcid_id,
                'full_name': full_name,
            }
            
            # Add optional fields
            if data and data.get('last-modified-date', {}) and data['last-modified-date'].get('value'):
                researcher_info['last_modified'] = data['last-modified-date']['value']
            
            # Add credit name if available
            if name_data and name_data.get('credit-name', {}) and name_data['credit-name'].get('value'):
                researcher_info['credit_name'] = name_data['credit-name']['value']
            
            # Add biography if available
            biography = data.get('biography', {}) if data else {}
            if biography and biography.get('content'):
                researcher_info['biography'] = biography['content']
            
            # Add keywords
            keywords = []
            keywords_data = data.get('keywords', {}) if data else {}
            for keyword in keywords_data.get('keyword', []):
                if isinstance(keyword, dict) and keyword.get('content'):
                    keywords.append(keyword['content'])
            researcher_info['keywords'] = keywords
            
            # Add alternative names
            alt_names = []
            other_names = data.get('other-names', {}) if data else {}
            for other_name in other_names.get('other-name', []):
                if isinstance(other_name, dict) and other_name.get('content'):
                    alt_names.append(other_name['content'])
            researcher_info['alternative_names'] = alt_names
            
            # Add external identifiers
            external_ids = {}
            ext_ids_data = data.get('external-identifiers', {}) if data else {}
            for ext_id in ext_ids_data.get('external-identifier', []):
                if isinstance(ext_id, dict):
                    id_type = ext_id.get('external-id-type', '').lower()
                    id_value = ext_id.get('external-id-value')
                    if id_type and id_value:
                        id_url = ext_id.get('external-id-url', {})
                        if isinstance(id_url, dict):
                            id_url = id_url.get('value')
                        external_ids[id_type] = ExternalId(
                            value=id_value,
                            url=id_url,
                            relationship=ext_id.get('external-id-relationship'),
                            visibility=ext_id.get('visibility')
                        )
            researcher_info['external_ids'] = external_ids
            
            # Add researcher URLs
            researcher_urls = []
            urls_data = data.get('researcher-urls', {}) if data else {}
            for url in urls_data.get('researcher-url', []):
                if isinstance(url, dict):
                    url_value = url.get('url', {})
                    if isinstance(url_value, dict):
                        url_value = url_value.get('value')
                    if url_value:
                        researcher_urls.append(ResearcherUrl(
                            name=url.get('url-name'),
                            url=url_value,
                            visibility=url.get('visibility')
                        ))
            researcher_info['researcher_urls'] = researcher_urls
            
            # Add email
            emails = data.get('emails', {}).get('email', []) if data else []
            for email in emails:
                if isinstance(email, dict) and email.get('email'):
                    researcher_info['email'] = EmailInfo(
                        address=email['email'],
                        verified=email.get('verified', False),
                        primary=email.get('primary', False),
                        visibility=email.get('visibility')
                    )
                    break
            
            # Add country
            addresses = data.get('addresses', {}).get('address', []) if data else []
            for address in addresses:
                if isinstance(address, dict):
                    country = address.get('country', {})
                    if isinstance(country, dict) and country.get('value'):
                        researcher_info['country'] = CountryInfo(
                            code=country['value'],
                            visibility=address.get('visibility')
                        )
                        break
            
            # Get education history from /education endpoint
            education = []
            try:
                education_response = requests.get(
                    f"{self.base_url}/{orcid_id}/educations",
                    headers=self.headers
                )
                education_response.raise_for_status()
                education_data = education_response.json()
                education_summaries = education_data.get('education-summary', [])
                for edu in education_summaries:
                    if isinstance(edu, dict):
                        org = edu.get('organization', {})
                        if org and org.get('name'):
                            education.append(AuthorAffiliation(
                                institution_name=org['name'],
                                department=edu.get('department-name'),
                                role=edu.get('role-title'),
                                start_date=self._parse_date(edu.get('start-date')),
                                end_date=self._parse_date(edu.get('end-date')),
                                visibility=edu.get('visibility')
                            ))
            except Exception as e:
                logging.error("Error fetching education data", exc_info=True)
            researcher_info['education'] = education
            
            # Get employment history from /employments endpoint
            affiliations = []
            try:
                employment_response = requests.get(
                    f"{self.base_url}/{orcid_id}/employments",
                    headers=self.headers
                )
                employment_response.raise_for_status()
                employment_data = employment_response.json()
                
                # Update to handle correct affiliation-group structure
                if employment_data and isinstance(employment_data, dict):
                    affiliation_groups = employment_data.get('affiliation-group', [])
                    for group in affiliation_groups:
                        if not isinstance(group, dict):
                            continue
                            
                        # Get summaries array from each affiliation group
                        summaries = group.get('summaries', [])
                        for summary in summaries:
                            # Get employment-summary from each summary item
                            emp = summary.get('employment-summary', {})
                            if isinstance(emp, dict):
                                org = emp.get('organization', {})
                                if isinstance(org, dict) and org.get('name'):
                                    affiliations.append(AuthorAffiliation(
                                        institution_name=org['name'],
                                        department=emp.get('department-name'),
                                        role=emp.get('role-title'),
                                        start_date=self._parse_date(emp.get('start-date')),
                                        end_date=self._parse_date(emp.get('end-date')),
                                        visibility=emp.get('visibility')
                                    ))
            except Exception as e:
                logging.error("Error fetching employment data", exc_info=True)
            researcher_info['affiliations'] = affiliations
            
            return AuthorMetadata(**researcher_info)
            
        except Exception as e:
            logging.error("Error fetching researcher info from ORCID", exc_info=True)
            # Return minimal AuthorMetadata object with error info
            return AuthorMetadata(
                orcid=orcid_id,
                full_name="Unknown",
                biography=f"Error fetching data: {str(e)}"
            )

    def _parse_date(self, date_dict: dict) -> str:
        """Helper method to parse ORCID date format to ISO format string"""
        if not date_dict:
            return None
        date_parts = []
        
        # Safely get year, month, day values handling None cases
        year_dict = date_dict.get('year')
        month_dict = date_dict.get('month')
        day_dict = date_dict.get('day')
        
        year = year_dict.get('value') if isinstance(year_dict, dict) else None
        month = month_dict.get('value') if isinstance(month_dict, dict) else None
        day = day_dict.get('value') if isinstance(day_dict, dict) else None
        
        # If we have a year but no month or day, add defaults to make a valid date
        if year:
            if not month:
                month = "01"
            if not day:
                day = "01"
            
            # Create ISO format date string YYYY-MM-DD
            return f"{year}-{month:0>2}-{day:0>2}"
        
        return None

    def fetch_author_metadata(self, orcid_id: str) -> dict:
        """
        Fetches raw researcher data from the ORCID API.
        :param orcid_id: ORCID ID.
        :return: Raw API response as a dictionary containing researcher data.
        """
        try:
            # Make request to ORCID API for person data
            person_response = requests.get(
                f"{self.base_url}/{orcid_id}/person",
                headers=self.headers
            )
            person_response.raise_for_status()
            person_data = person_response.json()

            # Make request for education data
            education_response = requests.get(
                f"{self.base_url}/{orcid_id}/educations",
                headers=self.headers
            )
            education_response.raise_for_status()
            education_data = education_response.json()

            # Make request for employment data
            employment_response = requests.get(
                f"{self.base_url}/{orcid_id}/employments",
                headers=self.headers
            )
            employment_response.raise_for_status()
            employment_data = employment_response.json()

            # Combine all data into a single response
            raw_data = {
                'person': person_data,
                'education': education_data,
                'employment': employment_data
            }

            return raw_data

        except Exception as e:
            logging.error("Error fetching raw researcher data from ORCID", exc_info=True)
            return {}

    def fetch_publications_by_orcid(self, orcid_id: str) -> dict:
        """
        Fetches raw publication data from the ORCID API.
        :param orcid_id: ORCID ID.
        :return: Raw API response as a dictionary containing publication data.
        """
        try:
            # Make request to ORCID API
            response = requests.get(
                f"{self.base_url}/{orcid_id}/works",
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logging.error("Error fetching raw publication data from ORCID", exc_info=True)
            return {}

    def get_publications_by_orcid(self, orcid_id: str) -> list:
        """
        Fetches a list of publications for the given ORCID ID.
        :param orcid_id: ORCID ID.
        :return: List of PaperMetadata objects with basic information.
        """
        
        try:
            # Make request to ORCID API
            response = requests.get(
                f"{self.base_url}/{orcid_id}/works",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            publications = []
            
            # Extract works from response
            work_groups = data.get('group', [])
            for work_group in work_groups:
                # Each work group contains work summaries - we'll take the first/preferred one
                work_summaries = work_group.get('work-summary', [])
                if not work_summaries:
                    continue
                    
                work = work_summaries[0]  # Get preferred work version
                
                # Extract title
                title = None
                title_obj = work.get('title', {})
                if isinstance(title_obj, dict):
                    title_value = title_obj.get('title', {})
                    if isinstance(title_value, dict):
                        title = title_value.get('value')
                
                if not title:  # Skip if no title
                    continue
                
                # Extract journal title
                journal = None
                journal_title = work.get('journal-title')  # Don't assume it's a dict
                if isinstance(journal_title, dict):
                    journal = journal_title.get('value')
                elif isinstance(journal_title, str):
                    journal = journal_title
                
                # Extract publication date
                pub_date = None
                date_obj = work.get('publication-date', {})
                if date_obj:
                    year_obj = date_obj.get('year', {})
                    month_obj = date_obj.get('month', {})
                    day_obj = date_obj.get('day', {})
                    
                    year = year_obj.get('value') if isinstance(year_obj, dict) else None
                    month = month_obj.get('value', '1') if isinstance(month_obj, dict) else '1'
                    day = day_obj.get('value', '1') if isinstance(day_obj, dict) else '1'
                    
                    if year:
                        try:
                            pub_date = datetime.strptime(
                                f"{year}-{month}-{day}", 
                                "%Y-%m-%d"
                            ).date()
                        except ValueError:
                            pass
                
                # Extract external identifiers
                external_ids = {}
                doi = None
                ext_ids_container = work.get('external-ids', {})
                if isinstance(ext_ids_container, dict):
                    for ext_id in ext_ids_container.get('external-id', []):
                        if isinstance(ext_id, dict):
                            id_type = ext_id.get('external-id-type', '').lower()
                            id_value = ext_id.get('external-id-value')
                            id_url = ext_id.get('external-id-url', {})
                            if isinstance(id_url, dict):
                                id_url = id_url.get('value')
                            
                            if id_type and id_value:
                                if id_type == 'doi':
                                    doi = id_value
                                external_ids[id_type] = {
                                    'value': id_value,
                                    'url': id_url
                                }
                
                # Create PaperMetadata object
                try:
                    paper = PaperMetadata(
                        title=title,
                        type=work.get('type'),
                        publication_date=pub_date,
                        journal=journal,
                        doi=doi,
                        external_ids=external_ids,
                        repository_source='ORCID',
                        url=work.get('url', {}).get('value') if isinstance(work.get('url'), dict) else None,
                        visibility=work.get('visibility')
                    )
                    publications.append(paper)
                except Exception as e:
                    print(f"Error creating PaperMetadata object: {str(e)}")
                    continue
            
            return publications
            
        except Exception as e:
            logging.error("Error fetching publications from ORCID", exc_info=True)
            return [] 