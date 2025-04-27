from typing import Optional, List, Literal
from pydantic import BaseModel, Field

# Define Literal types for each category
WetLabStatus = Literal["yes", "no", "mixed", "undetermined"]

BSLLevel = Literal[
    "bsl_1",     # Well-characterized agents not known to cause disease in healthy adults
    "bsl_2",     # Agents of moderate potential hazard to personnel and environment
    "bsl_3",     # Indigenous or exotic agents with potential for aerosol transmission
    "bsl_4",     # Dangerous/exotic agents with high risk of life-threatening disease
    "not_specified",  # BSL level not mentioned in publication
    "not_applicable"  # BSL classification not relevant to this work
]

DNAUseType = Literal[
    "gene_expression",      # Production of RNA/protein from synthetic DNA
    "cloning",              # Construction of recombinant DNA molecules
    "genome_editing",       # Modification of genomic DNA (CRISPR, etc.)
    "library_construction", # Creation of collections of DNA molecules
    "diagnostics",          # Development/use of diagnostic tests or assays
    "vaccine_development",  # Creation of vaccine candidates
    "therapeutics",         # Development of therapeutic agents
    "primers_probes",       # Use as primers or probes for PCR/hybridization
    "structure_studies",    # Investigation of DNA/RNA structure
    "metabolic_engineering", # Alteration of cellular metabolism
    "synthetic_biology",    # Engineering novel biological parts/systems
    "other_specified",      # Other use clearly specified in publication
    "not_specified"         # Use not clearly specified in publication
]

NovelSequenceUse = Literal[
    "yes", # Multiple previous publications with novel/hybrid sequences
    "no",   # One or few previous publications with novel/hybrid sequences
    "unclear"    # Cannot be determined from available publications
]

DNAType = Literal[
    "oligonucleotides",    # Short DNA sequences, typically <100bp
    "gene_fragments",      # Partial genes or genetic elements
    "complete_genes",      # Full-length genes
    "regulatory_elements", # Promoters, enhancers, etc.
    "vectors",             # Plasmids, viral vectors, etc.
    "whole_genome",        # Complete genomes or chromosomes
    "multiple_types",      # Combination of different DNA types
    "synthetic_genome",    # Fully or partially synthetic genome
    "other_specified",     # Other type clearly specified in publication
    "not_specified"        # Type not clearly specified in publication
]

class PaperClassificationMetadata(BaseModel):
    wet_lab_work: WetLabStatus = Field(
        ..., 
        description="Whether the publication involves wet lab work"
    )
    
    bsl_level: BSLLevel = Field(
        ..., 
        description="Highest Biosafety Level mentioned in the work"
    )
    
    dna_use: List[DNAUseType] = Field(
        ..., 
        description="How the synthetic DNA is being used"
    )
    
    novel_sequence_experience: NovelSequenceUse = Field(
        ..., 
        description="Researcher's experience with novel/hybrid sequences"
    )
    
    dna_type: List[DNAType] = Field(
        ..., 
        description="Type of synthetic DNA used in the research"
    )
    
    additional_notes: Optional[str] = Field(
        None, 
        description="Additional relevant information about the publication"
    )
