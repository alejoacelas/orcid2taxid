# %%
import logging
logging.getLogger('httpx').setLevel(logging.WARNING)

# %%

from orcid2taxid.analysis.extraction.paper import PaperExtractor
from tests.utils.load_data import load_test_papers
extractor = PaperExtractor()

papers = load_test_papers(n=3, force_refresh=True)
for paper in papers:
    print(paper.title)
    classification = extractor.extract_classification_from_abstract(paper)
    print(classification.model_dump_json(indent=2))

# %%

# %%
from orcid2taxid.core.operations.grant import find_grants
from orcid2taxid.core.models.schemas import ResearcherMetadata

researcher = ResearcherMetadata(
    orcid="0000-0001-9248-9365",
    given_name="Craig",
    family_name="Thompson",
    full_name="Craig Thompson",
)

researcher = find_grants(researcher, max_results=10)
for grant in researcher.grants:
    print(grant.model_dump_json(indent=2))

# %%
from orcid2taxid.integrations.nih_reporter import NIHReporterRepository

nih_reporter = NIHReporterRepository()
grant = nih_reporter.get_grant_by_number("R01 HG009906")   
if grant:
    print(f"Found grant: {grant.project_title}")
else:
    print("Grant not found")

# %%

from orcid2taxid.integrations.nsf_grants import NSFRepository
nsf_repository = NSFRepository()
grant = nsf_repository.get_grant_by_number("1244557")
if grant:
    print(f"Found grant: {grant.project_title}")
else:
    print("Grant not found")


# %%
from orcid2taxid.integrations.nsf_grants import NSFRepository
from tests.utils.load_data import load_test_researchers

nsf_grants = NSFRepository()

answer = nsf_grants.get_funding_by_pi_name('Jennifer Doudna')
for grant in answer:
    print(grant.model_dump_json(indent=2))

# %%
researcher = get_researcher_by_orcid(orcid)
raw_researcher_data = OrcidClient().fetch_author_metadata(orcid)
raw_publications_data = OrcidClient().fetch_publications_by_orcid(orcid)
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

