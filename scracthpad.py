# %%
from orcid2taxid.publication.integrations.epmc import get_epmc_publications_by_orcid
from orcid2taxid.grant.integrations.nih import get_nih_grant_by_number

orcid_id = "0000-0001-9248-9365"  # Example ORCID ID

# Test get_publications_by_orcid
print("Testing get_publications_by_orcid...")
papers = await get_epmc_publications_by_orcid(orcid_id, max_results=20)
print(papers)
for paper in papers:
    print(f"\nTitle: {paper.title}")
    print(f"DOI: {paper.doi}")
    print(f"Publication Date: {paper.publication_date}")
    print(f"Authors: {[author.researcher_id for author in paper.authors]}")
    print(f"Journal: {paper.journal_name}")
    print("-" * 80)

# Test NIH grant lookup
print("\nTesting NIH grant lookup...")
grant_id = "5R01AI139180-05"  # First grant ID from test cases
grant = await get_nih_grant_by_number(grant_id)
print(f"\nGrant details for {grant_id}:")
print(grant)


# %%

