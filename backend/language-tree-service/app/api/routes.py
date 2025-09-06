from fastapi import APIRouter, HTTPException
from typing import List
from app.services.wikipedia_service import fetch_language_relationships
from app.models.language import LanguageRelationship, LanguageInfo

router = APIRouter()

@router.get("/relationships/{language_name}/{depth}", response_model=List[LanguageRelationship])
async def get_language_relationships(language_name: str, depth: int):
    """
    Get language family relationships for a given language and depth.
    
    - **language_name**: Name of the language (e.g., "English", "Spanish")
    - **depth**: How many levels deep to explore (1-5)
    """
    if depth < 1 or depth > 5:
        raise HTTPException(status_code=400, detail="Depth must be between 1 and 5")
    
    print(f"Fetching relationships for {language_name} with depth {depth}")
    try:
        relationships = await fetch_language_relationships(language_name, depth)
        return relationships
    except Exception as e:
        print(f"Error fetching relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching relationships: {str(e)}")

# @router.get('/info/{language_name}', response_model=LanguageInfo)
# async def get_language_info(language_name: str):
#     """
#     Get detailed information about a specific language.
    
#     - **language_name**: Name of the language (e.g., "English", "Spanish")
#     """
#     print(f"Fetching info for {language_name}")
#     try:
#         language_info = await get_language_details(language_name)
#         if not language_info:
#             raise HTTPException(status_code=404, detail=f"Language '{language_name}' not found")
#         return language_info
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error fetching language info: {e}")
#         raise HTTPException(status_code=500, detail=f"Error fetching language info: {str(e)}")

@router.get('/health')
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "language-tree-service"}

@router.get('/stats')
async def get_service_stats():
    """Get service statistics"""
    return {
        "service": "language-tree-service",
        "version": "1.0.0",
        "endpoints": [
            "/relationships/{language_name}/{depth}",
            "/info/{language_name}",
            "/health",
            "/stats"
        ]
    }
