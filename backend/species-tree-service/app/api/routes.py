from fastapi import APIRouter, HTTPException
from typing import List
from app.services.wikipedia_service import fetch_species_relationships, get_species_details, get_taxonomic_classification
from app.models.species import TaxonomicRelationship, SpeciesInfo, TaxonomicClassification

router = APIRouter()

@router.get("/relationships/{species_name}/{depth}", response_model=List[TaxonomicRelationship])
async def get_species_relationships(species_name: str, depth: int):
    """
    Get taxonomic relationships for a given species and depth.
    
    - **species_name**: Name of the species (e.g., "Panthera leo", "Tiger", "Oak tree")
    - **depth**: How many levels deep to explore (1-6)
    """
    if depth < 1 or depth > 6:
        raise HTTPException(status_code=400, detail="Depth must be between 1 and 6")
    
    print(f"Fetching relationships for {species_name} with depth {depth}")
    try:
        relationships = await fetch_species_relationships(species_name, depth)
        if not relationships:
            raise HTTPException(status_code=404, detail=f"No taxonomic data found for '{species_name}'")
        return relationships
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching relationships: {str(e)}")

@router.get('/info/{species_name}', response_model=SpeciesInfo)
async def get_species_info(species_name: str):
    """
    Get detailed information about a specific species.
    
    - **species_name**: Name of the species (e.g., "Panthera leo", "Tiger", "Oak tree")
    """
    print(f"Fetching info for {species_name}")
    try:
        species_info = await get_species_details(species_name)
        if not species_info:
            raise HTTPException(status_code=404, detail=f"Species '{species_name}' not found")
        return species_info
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching species info: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching species info: {str(e)}")

@router.get('/taxonomy/{species_name}', response_model=TaxonomicClassification)
async def get_taxonomic_classification_endpoint(species_name: str):
    """
    Get complete taxonomic classification for a species.
    
    - **species_name**: Name of the species (e.g., "Panthera leo", "Tiger", "Oak tree")
    """
    print(f"Fetching taxonomic classification for {species_name}")
    try:
        from app.services.wikipedia_service import get_species_qid
        qid = get_species_qid(species_name)
        if not qid:
            raise HTTPException(status_code=404, detail=f"Species '{species_name}' not found")
        
        classification = await get_taxonomic_classification(qid)
        if not classification:
            raise HTTPException(status_code=404, detail=f"No taxonomic classification found for '{species_name}'")
        return classification
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching taxonomic classification: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching taxonomic classification: {str(e)}")

@router.get('/health')
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "species-tree-service"}

@router.get('/stats')
async def get_service_stats():
    """Get service statistics"""
    return {
        "service": "species-tree-service",
        "version": "1.0.0",
        "endpoints": [
            "/relationships/{species_name}/{depth}",
            "/info/{species_name}",
            "/taxonomy/{species_name}",
            "/health",
            "/stats"
        ],
        "supported_taxa": [
            "Animals (Kingdom Animalia)",
            "Plants (Kingdom Plantae)", 
            "Fungi (Kingdom Fungi)",
            "Bacteria (Kingdom Bacteria)",
            "Archaea (Kingdom Archaea)",
            "Protists (various kingdoms)"
        ]
    }
