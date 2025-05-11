from orcid2taxid.publication.schemas import PublicationRecord
from orcid2taxid.llm.extractors.organism_mention import extract_organisms_from_publication
from orcid2taxid.taxonomy.integrations import get_taxonomy_info
from orcid2taxid.core.logging import get_logger, log_event

logger = get_logger(__name__)

@log_event(__name__)
async def collect_publication_organisms(
    publication: PublicationRecord,
    include_taxonomy: bool = True
) -> PublicationRecord:
    """
    Process a publication to extract organisms and add taxonomy information.
    
    This function extracts organisms from the publication using an LLM
    and then adds taxonomy information for each organism if requested.
    
    Args:
        publication: The publication record to process
        include_taxonomy: Whether to include taxonomy information (default: True)
        
    Returns:
        PublicationRecord: The updated publication record with organisms and taxonomy
    """
    if not publication.abstract:
        logger.warning("Publication has no abstract, skipping organism extraction")
        return publication
    
    organism_list = await extract_organisms_from_publication(publication)
    publication.organisms = organism_list.organisms
    
    if include_taxonomy and publication.organisms:
        for organism in publication.organisms:
            taxonomy_info = await get_taxonomy_info(organism.searchable_term)
            organism.taxonomy = taxonomy_info
    
    return publication
