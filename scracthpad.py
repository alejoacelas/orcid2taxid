# %%

from orcid2taxid.llm.extractors.customer_search import search_customer_information
from orcid2taxid.researcher.services import get_customer_profile
from orcid2taxid.shared.schemas import ResearcherID

customer_id = ResearcherID(
    given_name="Adib",
    family_name="Hasan",
    orcid="0009-0009-2183-7559"
)
customer = await get_customer_profile(customer_id)
search_result = await search_customer_information(customer)

# %%

print(search_result.model_dump_json(indent=2))


# %%
from orcid2taxid.publication.integrations.epmc import get_epmc_publications_by_orcid
from orcid2taxid.llm.extractors.organism_mention import extract_organisms_from_publication

orcid_id = "0000-0001-9248-9365"  # Example ORCID ID

# Test get_publications_by_orcid
print("Testing get_publications_by_orcid...")
papers = await get_epmc_publications_by_orcid(orcid_id, max_results=2)
print(papers)
for paper in papers:
    organisms = await extract_organisms_from_publication(paper)
    if len(organisms.organisms) > 0:
        print(f"\nTitle: {paper.title}")
        for organism in organisms.organisms:
            print(f"Organism: {organism.model_dump_json()}")
        
        # print(f"DOI: {paper.doi}")
        # print(f"Publication Date: {paper.publication_date}")
        # print(f"Authors: {[author.researcher_id for author in paper.authors]}")
        # print(f"Journal: {paper.journal_name}")
    # print("-" * 80)

# %%
from orcid2taxid.grant.integrations.nih import get_nih_grant_by_number

# Test NIH grant lookup
print("\nTesting NIH grant lookup...")
grant_id = "5R01AI139180-05"  # First grant ID from test cases
grant = await get_nih_grant_by_number(grant_id)
print(f"\nGrant details for {grant_id}:")
print(grant)


# %%

from orcid2taxid.taxonomy.integrations.ncbi import (
    fetch_taxonomy_record,
    fetch_taxid_search,
    get_taxonomy_info
)


print("Testing NCBI Taxonomy API...")
    
# Test organisms
organisms = [
    "Homo sapiens",  # Human
    "Mus musculus",  # Mouse
    "Escherichia coli",  # Common bacteria
    "SARS-CoV-2"     # COVID-19 virus
]

# Test 1: Search for taxonomy IDs
print("\n=== Testing taxonomy ID search ===")
for organism in organisms:
    print(f"\nSearching for: {organism}")
    search_result = await fetch_taxid_search(organism)
    print(f"Found {len(search_result.id_list)} results")
    print(f"Taxonomy IDs: {search_result.id_list[:5]}")

# Test 2: Fetch taxonomy record by ID
print("\n=== Testing taxonomy record fetch ===")
# Human taxonomy ID
taxid = "9606"
print(f"\nFetching taxonomy record for ID: {taxid}")
taxonomy_response = await fetch_taxonomy_record(taxid)
tax_record = taxonomy_response.result.get(taxid)
print(f"Scientific name: {tax_record.scientific_name}")
print(f"Rank: {tax_record.rank}")
print(f"Division: {tax_record.division}")

# Test 3: Get comprehensive taxonomy info
print("\n=== Testing comprehensive taxonomy info ===")
for organism in organisms:
    print(f"\nGetting taxonomy info for: {organism}")
    taxonomy_info = await get_taxonomy_info(organism)
    print(f"Taxonomy ID: {taxonomy_info.taxid}")
    print(f"Scientific name: {taxonomy_info.scientific_name}")
    print(f"Rank: {taxonomy_info.rank}")
    if taxonomy_info.lineage:
        print(f"Lineage: {' > '.join(taxonomy_info.lineage[-3:])}")

# %%
