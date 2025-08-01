from typing import List, Dict
from app.services.wikipedia_service import fetch_species_relationships

class SpeciesTreeService:
    """Service for handling species tree operations"""
    
    def __init__(self):
        pass

    async def get_species_relationships(self, species_name: str, depth: int) -> List[Dict[str, str]]:
        """Get taxonomic relationships for a given species and depth"""
        relationships = await fetch_species_relationships(species_name, depth)
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

    async def get_taxonomic_tree(self, species_name: str, depth: int) -> Dict:
        """Get complete taxonomic tree data"""
        relationships = await self.get_species_relationships(species_name, depth)
        return {
            "root_species": species_name,
            "depth": depth,
            "relationships": relationships,
            "total_relationships": len(relationships)
        }
