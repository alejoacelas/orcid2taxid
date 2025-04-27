# %%
import asyncio
from orcid2taxid.integrations.epmc_publications import get_publications_by_orcid, get_publications_by_researcher_metadata
from orcid2taxid.core.models.base_schemas import ResearcherProfile

# Test with a known ORCID ID
orcid_id = "0000-0002-7115-407X"  # Example ORCID ID

# Test get_publications_by_orcid
print("Testing get_publications_by_orcid...")
papers = await get_publications_by_orcid(orcid_id, max_results=2)
for paper in papers:
    print(f"\nTitle: {paper.title}")
    print(f"DOI: {paper.doi}")
    print(f"Publication Date: {paper.publication_date}")
    print(f"Authors: {[author.researcher_id for author in paper.authors]}")
    print(f"Journal: {paper.journal_name}")
    print("-" * 80)

# # Test with researcher metadata
# print("\nTesting get_publications_by_researcher_metadata...")
# researcher = ResearcherProfile(
#     orcid=orcid_id,
#     given_name="Craig",
#     family_name="Thompson",
#     full_name="Thompson, Craig"
# )
# papers = await get_publications_by_researcher_metadata(researcher.model_dump(), max_results=2)
# for paper in papers:
#     print(f"\nTitle: {paper.title}")
#     print(f"DOI: {paper.doi}")
#     print(f"Publication Date: {paper.publication_date}")
#     print(f"Authors: {[author.full_name for author in paper.authors]}")
#     print(f"Journal: {paper.journal_name}")
#     print("-" * 80)


# %%
