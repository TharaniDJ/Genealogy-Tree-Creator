from typing import List, Dict
from app.services.wikipedia_service import fetch_relationships

class GenealogyService:
    def __init__(self):
        pass

    def get_relationships(self, page_title: str, depth: int) -> List[Dict[str, str]]:
        relationships = fetch_relationships(page_title, depth)
        formatted_relationships = self.format_relationships(relationships)
        return formatted_relationships

    def format_relationships(self, relationships: List[List[str]]) -> List[Dict[str, str]]:
        formatted = []
        for entity1, relationship, entity2 in relationships:
            formatted.append({
                "entity1": entity1,
                "relationship": relationship,
                "entity2": entity2
            })
        return formatted