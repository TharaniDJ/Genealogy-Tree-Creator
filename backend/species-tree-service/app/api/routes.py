from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.taxonomy import (
    TaxonomyResponse, 
    TaxonomyTuplesResponse, 
    ExpansionResponse, 
    ExpansionRequest,
    ErrorResponse
)
from app.services.taxonomy_extractor import TaxonomyExtractor
from app.services.taxonomy_expander import TaxonomyExpander

router = APIRouter()

# Initialize services
taxonomy_extractor = TaxonomyExtractor()
taxonomy_expander = TaxonomyExpander()

@router.get("/taxonomy/{scientific_name}", response_model=TaxonomyTuplesResponse)
async def get_taxonomies(scientific_name: str):
    """
    Get complete taxonomic hierarchy for a species in tuple format.
    
    - **scientific_name**: Scientific name of the species (e.g., "Homo sapiens", "Panthera leo")
    
    Returns taxonomic relationships as tuples (parent_taxon, has_child, child_taxon)
    """
    print(f"📊 Extracting taxonomy tuples for: {scientific_name}")
    
    try:
        result = taxonomy_extractor.extract_as_tuples(scientific_name)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not extract taxonomic information for '{scientific_name}'. Please check the scientific name and try again."
            )
        
        print(f"✅ Successfully extracted {result.total_relationships} taxonomic relationships")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error extracting taxonomy: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error while extracting taxonomy: {str(e)}"
        )

# @router.get("/taxonomy/{scientific_name}/detailed", response_model=TaxonomyResponse)
# async def get_detailed_taxonomy(scientific_name: str):
#     """
#     Get detailed taxonomic hierarchy for a species with full information.
    
#     - **scientific_name**: Scientific name of the species (e.g., "Homo sapiens", "Panthera leo")
    
#     Returns complete taxonomic information including ranks, names, and Wikipedia links
#     """
#     print(f"📊 Extracting detailed taxonomy for: {scientific_name}")
    
#     try:
#         result = taxonomy_extractor.extract_taxonomy_realtime(scientific_name)
        
#         if not result:
#             raise HTTPException(
#                 status_code=404, 
#                 detail=f"Could not extract taxonomic information for '{scientific_name}'. Please check the scientific name and try again."
#             )
        
#         print(f"✅ Successfully extracted {result.total_taxa_found} taxonomic entries")
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ Error extracting detailed taxonomy: {e}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Internal error while extracting taxonomy: {str(e)}"
#         )

@router.get("/expand/{taxon_name}/{rank}", response_model=ExpansionResponse)
async def expand_taxonomies(taxon_name: str, rank: str, target_rank: Optional[str] = None):
    """
    Expand taxonomic tree from a given taxon and rank to show children.
    
    - **taxon_name**: Name of the taxonomic entity (e.g., "Mammalia", "Carnivora")
    - **rank**: Current taxonomic rank (e.g., "class", "order", "family")
    - **target_rank**: Optional target rank to expand to (e.g., "order", "family", "genus")
    
    Returns children of the given taxon in tuple format (parent_taxon, has_child, child_taxon)
    """
    print(f"🔍 Expanding taxonomy from {taxon_name} ({rank}) to {target_rank or 'next rank'}")
    
    try:
        # Validate rank
        valid_ranks = taxonomy_expander.taxonomic_ranks
        if rank.lower() not in valid_ranks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rank '{rank}'. Valid ranks are: {', '.join(valid_ranks)}"
            )
        
        if target_rank and target_rank.lower() not in valid_ranks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target rank '{target_rank}'. Valid ranks are: {', '.join(valid_ranks)}"
            )
        
        result = taxonomy_expander.expand_taxonomy(taxon_name, rank, target_rank)
        
        print(f"✅ Successfully found {result.total_children} children")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error expanding taxonomy: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error while expanding taxonomy: {str(e)}"
        )

@router.get("/expand/domains", response_model=List[str])
async def get_domains():
    """
    Get all biological domains.
    
    Returns list of domain names
    """
    try:
        domains = taxonomy_expander.get_domain()
        return domains
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting domains: {str(e)}"
        )

@router.get("/expand/kingdoms", response_model=List[str])
async def get_kingdoms(domain: Optional[str] = None):
    """
    Get kingdoms, optionally filtered by domain.
    
    - **domain**: Optional domain name to filter by (e.g., "Eukarya", "Bacteria", "Archaea")
    
    Returns list of kingdom names
    """
    try:
        kingdoms = taxonomy_expander.get_kingdom(domain)
        return kingdoms
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting kingdoms: {str(e)}"
        )

@router.get("/ranks", response_model=List[str])
async def get_taxonomic_ranks():
    """
    Get all available taxonomic ranks in hierarchical order.
    
    Returns list of taxonomic ranks from domain to strain
    """
    try:
        return taxonomy_expander.taxonomic_ranks
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting taxonomic ranks: {str(e)}"
        )