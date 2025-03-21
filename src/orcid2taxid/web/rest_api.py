from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.get("/orcid2taxid/{orcid_id}", response_model=List['OrganismList'])
def get_taxids_for_orcid(orcid_id: str) -> List['OrganismList']:
    """
    REST endpoint to retrieve TAXIDs for a researcher identified by ORCID.
    :param orcid_id: ORCID of the researcher.
    :return: JSON response with mapped TAXIDs and relevant info.
    """
    pass