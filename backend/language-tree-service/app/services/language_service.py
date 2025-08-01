from typing import List, Dict
from app.services.wikipedia_service import fetch_language_relationships

class LanguageTreeService:
    """Service for handling language tree operations"""
    
    def __init__(self):
        pass

    async def get_language_relationships(self, language_name: str, depth: int) -> List[Dict[str, str]]:
        """Get language relationships for a given language and depth"""
        relationships = await fetch_language_relationships(language_name, depth)
        return relationships

    def format_relationships(self, relationships: List[List[str]]) -> List[Dict[str, str]]:
        """Format relationships from list format to dictionary format"""
        formatted = []
        for entity1, relationship, entity2 in relationships:
            formatted.append({
                "entity1": entity1,
                "relationship": relationship,
                "entity2": entity2
            })
        return formatted

    async def get_language_family_tree(self, language_name: str, depth: int) -> Dict:
        """Get complete language family tree data"""
        relationships = await self.get_language_relationships(language_name, depth)
        return {
            "root_language": language_name,
            "depth": depth,
            "relationships": relationships,
            "total_relationships": len(relationships)
        }
