# %%
import logging

from orcid2taxid.core.operations.researcher import get_researcher_by_orcid, find_publications
from orcid2taxid.core.operations.paper import get_taxonomy_info

from orcid2taxid.analysis.extraction.paper import PaperExtractor
from orcid2taxid.analysis.extraction.researcher import ResearcherExtractor
from tests.utils.load_data import load_test_orcids, load_test_papers, load_test_researchers

from orcid2taxid.integrations.orcid import OrcidClient

# Quiet logging from Anthropic API calls
logging.getLogger('httpx').setLevel(logging.WARNING)


orcid = "0009-0009-2183-7559"

# %%
researcher = get_researcher_by_orcid(orcid)
raw_researcher_data = OrcidClient().fetch_author_metadata(orcid)
raw_publications_data = OrcidClient().fetch_publications_by_orcid(orcid)

# %%
from orcid2taxid.integrations.nih_reporter import NIHReporterRepository
from tests.utils.load_data import load_test_researchers

researchers = load_test_researchers(n=20, force_refresh=True)
nih_reporter = NIHReporterRepository()

answer = nih_reporter.get_funding_by_pi_name("Craig Thompson")
print(answer)

# %%
import logging
logging.getLogger('httpx').setLevel(logging.WARNING)

from orcid2taxid.core.operations.grant import find_grants
from tests.utils.load_data import load_test_researchers

researchers = load_test_researchers(n=50)
test_researcher = researchers[10]

test_researcher.given_name = "Craig"
test_researcher.family_name = "Thompson"
test_researcher = find_grants(test_researcher, max_results=10)

print(test_researcher.grants.to_json())

# %%



# %%
# for researcher in researchers[1:]:
#     test_researcher = find_grants(researcher, max_results=10)
#     print(researcher.full_name, len(researcher.grants))

# %%

from tests.utils.load_data import load_test_papers

papers = load_test_papers(n=50, force_refresh=True)

# %%

