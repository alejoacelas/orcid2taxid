# %%
import logging

from orcid2taxid.researchers.services import get_researcher_by_orcid, find_publications
from orcid2taxid.publications.services import get_taxonomy_info

from orcid2taxid.analysis.extraction.paper import PaperExtractor
from orcid2taxid.analysis.extraction.researcher import ResearcherExtractor
from tests.utils.load_data import load_test_orcids, load_test_papers, load_test_researchers

# Quiet logging from Anthropic API calls
logging.getLogger('httpx').setLevel(logging.WARNING)

# %%
test_orcids = load_test_orcids(n=4, keyword="virology")
paper_extractor = PaperExtractor()

for orcid in test_orcids:
    # Get researcher metadata
    researcher = get_researcher_by_orcid(orcid)
    # Fill researcher.publications with papers from Europe PMC
    researcher = find_publications(researcher)
    
    print(f"### AUTHOR: {researcher.full_name} ({researcher.orcid})")
    print(f"    Found {len(researcher.publications)} publications\n")

    if researcher.publications:
        print("    ### ORGANISMS")
    for paper in researcher.publications:
        organisms = paper_extractor.extract_organisms_from_abstract(paper)
        for org in organisms:
            # You can use to_json to print any researcher, paper or organism
            print(org.to_json(indent=2))

# %%

test_papers = load_test_papers(n=2, keyword="jensen")
paper_extractor = PaperExtractor()

for paper in test_papers:
    print(f"### PAPER: {paper.title}")
    organisms = paper_extractor.extract_organisms_from_abstract(paper)
    if not organisms:
        print("    No organisms found")
    else:
        print("    Found organisms:")
        for org in organisms:
            print(f"        {org.searchable_name} ({org.confidence})")
    
    paper_with_taxonomy = get_taxonomy_info(paper)
    print("Paper with added taxonomy info:")
    print("Organisms with taxonomy info:")
    for org in paper_with_taxonomy.organisms:
        if org.taxonomy_info:
            print(f"    {org.searchable_name}: {org.taxonomy_info.scientific_name} (TaxID: {org.taxonomy_info.taxid})")
    print("\n")
    print(paper_with_taxonomy.to_json(indent=2))

# %%

test_researchers = load_test_researchers(n=5, keyword="jensen")
researcher_extractor = ResearcherExtractor()

for researcher in test_researchers:
    bio = researcher_extractor.generate_researcher_bio(researcher)
    print(f"### AUTHOR: {researcher.full_name} ({researcher.orcid})")
    print(f"    Bio: {bio['short_bio']}")
    print(f"    Research focus: {bio['research_focus']}\n")
# %%
