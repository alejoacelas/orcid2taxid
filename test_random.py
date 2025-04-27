# %%
from orcid2taxid.publications.integrations.epmc import get_publications_by_orcid

# Test with a known ORCID ID
orcid_id = "0000-0001-9248-9365"  # Example ORCID ID

# Test get_publications_by_orcid
print("Testing get_publications_by_orcid...")
papers = await get_publications_by_orcid(orcid_id, max_results=20)
print(papers)
for paper in papers:
    print(f"\nTitle: {paper.title}")
    print(f"DOI: {paper.doi}")
    print(f"Publication Date: {paper.publication_date}")
    print(f"Authors: {[author.researcher_id for author in paper.authors]}")
    print(f"Journal: {paper.journal_name}")
    print("-" * 80)


# %%
