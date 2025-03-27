from typing import List, Optional
import asyncio
from orcid2taxid.core.models.schemas import PaperMetadata, PaperClassificationMetadata
from orcid2taxid.analysis.extraction.paper import PaperExtractor
from orcid2taxid.integrations.ncbi import TaxIDLookup

# Singleton instances
_paper_extractor = PaperExtractor()
_taxid_lookup = TaxIDLookup()

async def get_organisms_async(paper: PaperMetadata) -> PaperMetadata:
    """
    Extract organisms from a paper's abstract asynchronously.
    
    :param paper: The paper metadata
    :return: Updated paper with organisms field populated
    """
    if not paper.abstract:
        # Skip papers without abstracts
        return paper
        
    paper.organisms = await _paper_extractor.extract_organisms_from_abstract(paper)
    return paper

def get_organisms(paper: PaperMetadata) -> PaperMetadata:
    """
    Extract organisms from a paper's abstract.
    This is a thin wrapper around get_organisms_async.
    
    :param paper: The paper metadata
    :return: Updated paper with organisms field populated
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_organisms_async(paper))
    finally:
        loop.close()

async def get_classification_async(paper: PaperMetadata) -> PaperMetadata:
    """
    Classify a paper based on its abstract asynchronously.
    
    :param paper: The paper metadata
    :return: Updated paper with classification field populated
    """
    if not paper.abstract:
        # Skip papers without abstracts
        return paper
        
    paper.classification = await _paper_extractor.extract_classification_from_abstract(paper)
    return paper

def get_classification(paper: PaperMetadata) -> PaperMetadata:
    """
    Classify a paper based on its abstract.
    This is a thin wrapper around get_classification_async.
    
    :param paper: The paper metadata
    :return: Updated paper with classification field populated
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_classification_async(paper))
    finally:
        loop.close()

async def get_taxonomy_info_async(paper: PaperMetadata) -> PaperMetadata:
    """
    Get taxonomy information for organisms in a paper asynchronously.
    
    :param paper: The paper metadata with organisms field populated
    :return: Updated paper with taxonomy information added to organisms
    """
    if not paper.organisms:
        return paper
        
    for organism in paper.organisms:
        if not organism.taxonomy_info:  # Only get taxonomy info if not already present
            tax_info = _taxid_lookup.get_taxid(organism.searchable_name)
            if tax_info:
                organism.taxonomy_info = tax_info
                
    return paper

def get_taxonomy_info(paper: PaperMetadata) -> PaperMetadata:
    """
    Get taxonomy information for organisms in a paper.
    This is a thin wrapper around get_taxonomy_info_async.
    
    :param paper: The paper metadata with organisms field populated
    :return: Updated paper with taxonomy information added to organisms
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_taxonomy_info_async(paper))
    finally:
        loop.close()

async def process_paper_async(paper: PaperMetadata) -> PaperMetadata:
    """
    Process a paper asynchronously by extracting organisms and classification in parallel.
    
    :param paper: The paper metadata to process
    :return: Updated paper with organisms and classification
    """
    # Process paper using the async method
    processed_paper = await _paper_extractor.process_paper(paper)
    
    # Get taxonomy info (currently sync)
    processed_paper = await get_taxonomy_info_async(processed_paper)
    
    return processed_paper

def find_full_text_url(paper: PaperMetadata) -> PaperMetadata:
    """Find the full text URL for the paper using Unpaywall"""
    # TODO: Implement Unpaywall integration
    return paper 