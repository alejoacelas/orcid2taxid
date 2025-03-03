# %%
from orcid2taxid.data.clients.orcid_client import OrcidClient
from orcid2taxid.data.repositories.europe_pmc import EuropePMCRepository
from orcid2taxid.data.repositories.biorxiv import BiorxivRepository
from orcid2taxid.core.models.schemas import AuthorMetadata, AuthorAffiliation
from orcid2taxid.core.config.logging import setup_logging
from tests.utils.load_data import load_test_orcids, load_test_author_metadata
import json
from pathlib import Path
import logging

# Set up logging
setup_logging()

# %%
# test_orcids = load_test_orcids(10)
# orcid_client = OrcidClient()
# raw_author_metadata = [orcid_client.fetch_author_metadata(orcid) for orcid in test_orcids]
# author_metadata = [orcid_client.get_author_metadata(orcid) for orcid in test_orcids]
# # print(json.dumps(raw_author_metadata[0], indent=4))
# print(author_metadata[0].model_dump_json(indent=4))
# %%
author_metadata = load_test_author_metadata(5)
repository = BiorxivRepository()
raw_paper_metadata = [repository.fetch_publications_by_author_metadata(am, max_results=2) for am in author_metadata]
paper_metadata = [repository.get_publications_by_author_metadata(am, max_results=2) for am in author_metadata]
# %%
# test_orcids = load_test_orcids(5)
# repository = EuropePMCRepository()
# raw_paper_metadata = [repository.fetch_publications_by_orcid(orcid, max_results=2) for orcid in test_orcids]
# paper_metadata = [repository.get_publications_by_orcid(orcid, max_results=2) for orcid in test_orcids]

# %%
# print(json.dumps(raw_paper_metadata[0], indent=4))

# %%
# print(json.dumps(paper_metadata[0].model_dump_json(indent=4)))

# %%
