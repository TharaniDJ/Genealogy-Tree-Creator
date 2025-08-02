from typing import List, Dict, Set, Optional
import re

def validate_language_name(language_name: str) -> str:
    """Validate and normalize language name"""
    if not language_name or not language_name.strip():
        raise ValueError("Language name cannot be empty")
    
    # Remove extra whitespace and capitalize properly
    normalized = " ".join(language_name.strip().split())
    return normalized.title()

def validate_depth(depth: int) -> int:
    """Validate depth parameter"""
    if not isinstance(depth, int):
        raise ValueError("Depth must be an integer")
    
    if depth < 1:
        raise ValueError("Depth must be at least 1")
    
    if depth > 5:
        raise ValueError("Depth cannot exceed 5")
    
    return depth

def format_relationship_data(relationships: List[Dict[str, str]]) -> Dict:
    """Format relationship data for API response"""
    unique_entities = set()
    relationship_types = set()
    
    for rel in relationships:
        unique_entities.add(rel["entity1"])
        unique_entities.add(rel["entity2"])
        relationship_types.add(rel["relationship"])
    
    return {
        "relationships": relationships,
        "summary": {
            "total_relationships": len(relationships),
            "unique_entities": len(unique_entities),
            "relationship_types": list(relationship_types)
        }
    }

def extract_qid_from_uri(uri: str) -> Optional[str]:
    """Extract QID from Wikidata URI"""
    if not uri:
        return None
    
    # Match patterns like http://www.wikidata.org/entity/Q123456
    match = re.search(r'/entity/(Q\d+)', uri)
    if match:
        return match.group(1)
    
    # Direct QID
    if uri.startswith('Q') and uri[1:].isdigit():
        return uri
    
    return None

def build_language_hierarchy(relationships: List[Dict[str, str]]) -> Dict:
    """Build hierarchical structure from flat relationship list"""
    hierarchy = {}
    
    # Group by relationship type
    by_type = {}
    for rel in relationships:
        rel_type = rel["relationship"]
        if rel_type not in by_type:
            by_type[rel_type] = []
        by_type[rel_type].append(rel)
    
    return by_type

def deduplicate_relationships(relationships: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate relationships"""
    seen = set()
    unique = []
    
    for rel in relationships:
        # Create a tuple for comparison (normalize order for bidirectional relationships)
        key = (rel["entity1"], rel["relationship"], rel["entity2"])
        reverse_key = (rel["entity2"], rel["relationship"], rel["entity1"])
        
        if key not in seen and reverse_key not in seen:
            seen.add(key)
            unique.append(rel)
    
    return unique

def filter_relationships_by_type(relationships: List[Dict[str, str]], 
                                allowed_types: Set[str]) -> List[Dict[str, str]]:
    """Filter relationships by allowed relationship types"""
    return [
        rel for rel in relationships 
        if rel["relationship"] in allowed_types
    ]

def get_language_statistics(relationships: List[Dict[str, str]]) -> Dict:
    """Generate statistics from language relationships"""
    if not relationships:
        return {
            "total_relationships": 0,
            "unique_languages": 0,
            "relationship_types": [],
            "most_connected_language": None
        }
    
    # Count connections per language
    connections = {}
    relationship_types = set()
    
    for rel in relationships:
        entity1, entity2 = rel["entity1"], rel["entity2"]
        relationship_types.add(rel["relationship"])
        
        connections[entity1] = connections.get(entity1, 0) + 1
        connections[entity2] = connections.get(entity2, 0) + 1
    
    # Find most connected language
    most_connected = max(connections.items(), key=lambda x: x[1]) if connections else None
    
    return {
        "total_relationships": len(relationships),
        "unique_languages": len(connections),
        "relationship_types": list(relationship_types),
        "most_connected_language": {
            "name": most_connected[0],
            "connections": most_connected[1]
        } if most_connected else None
    }

def sanitize_string(text: str) -> str:
    """Sanitize string for safe usage"""
    if not text:
        return ""
    
    # Remove control characters and normalize whitespace
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    sanitized = re.sub(r'\s+', ' ', sanitized)
    return sanitized.strip()

def create_error_response(message: str, error_code: str = None) -> Dict:
    """Create standardized error response"""
    response = {
        "error": True,
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
    
    return response
