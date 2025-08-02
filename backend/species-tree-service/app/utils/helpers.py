from typing import List, Dict, Set, Optional
import re

def validate_species_name(species_name: str) -> str:
    """Validate and normalize species name"""
    if not species_name or not species_name.strip():
        raise ValueError("Species name cannot be empty")
    
    # Remove extra whitespace and normalize
    normalized = " ".join(species_name.strip().split())
    
    # Handle scientific names (Genus species) vs common names
    if is_scientific_name(normalized):
        return format_scientific_name(normalized)
    else:
        return normalized.title()

def is_scientific_name(name: str) -> bool:
    """Check if name appears to be a scientific name (binomial nomenclature)"""
    # Scientific names typically have 2 parts: Genus species
    parts = name.split()
    if len(parts) == 2:
        # First part (genus) should be capitalized, second (species) lowercase
        return parts[0][0].isupper() and parts[1][0].islower()
    return False

def format_scientific_name(name: str) -> str:
    """Format scientific name according to binomial nomenclature rules"""
    parts = name.split()
    if len(parts) >= 2:
        # Genus capitalized, species lowercase
        genus = parts[0].capitalize()
        species = parts[1].lower()
        return f"{genus} {species}"
    return name

def validate_depth(depth: int) -> int:
    """Validate depth parameter for taxonomic queries"""
    if not isinstance(depth, int):
        raise ValueError("Depth must be an integer")
    
    if depth < 1:
        raise ValueError("Depth must be at least 1")
    
    if depth > 6:
        raise ValueError("Depth cannot exceed 6 for taxonomic queries")
    
    return depth

def format_taxonomic_data(relationships: List[Dict[str, str]]) -> Dict:
    """Format taxonomic relationship data for API response"""
    unique_taxa = set()
    relationship_types = set()
    
    for rel in relationships:
        unique_taxa.add(rel["entity1"])
        unique_taxa.add(rel["entity2"])
        relationship_types.add(rel["relationship"])
    
    return {
        "relationships": relationships,
        "summary": {
            "total_relationships": len(relationships),
            "unique_taxa": len(unique_taxa),
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

def build_taxonomic_hierarchy(relationships: List[Dict[str, str]]) -> Dict:
    """Build hierarchical taxonomic structure from flat relationship list"""
    hierarchy = {}
    
    # Group by relationship type
    by_type = {}
    for rel in relationships:
        rel_type = rel["relationship"]
        if rel_type not in by_type:
            by_type[rel_type] = []
        by_type[rel_type].append(rel)
    
    return by_type

def get_taxonomic_rank_order() -> List[str]:
    """Get taxonomic ranks in hierarchical order"""
    return [
        "kingdom",
        "phylum", 
        "class",
        "order",
        "family",
        "genus",
        "species",
        "subspecies"
    ]

def normalize_taxonomic_classification(classification: Dict[str, str]) -> Dict[str, str]:
    """Normalize taxonomic classification by removing None values and standardizing"""
    normalized = {}
    rank_order = get_taxonomic_rank_order()
    
    for rank in rank_order:
        value = classification.get(rank) or classification.get(f"{rank}_name")
        if value and value.strip():
            normalized[rank] = value.strip()
    
    return normalized

def deduplicate_relationships(relationships: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate taxonomic relationships"""
    seen = set()
    unique = []
    
    for rel in relationships:
        # Create a tuple for comparison
        key = (rel["entity1"], rel["relationship"], rel["entity2"])
        
        if key not in seen:
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

def get_species_statistics(relationships: List[Dict[str, str]]) -> Dict:
    """Generate statistics from species relationships"""
    if not relationships:
        return {
            "total_relationships": 0,
            "unique_taxa": 0,
            "relationship_types": [],
            "most_connected_taxon": None
        }
    
    # Count connections per taxon
    connections = {}
    relationship_types = set()
    
    for rel in relationships:
        entity1, entity2 = rel["entity1"], rel["entity2"]
        relationship_types.add(rel["relationship"])
        
        connections[entity1] = connections.get(entity1, 0) + 1
        connections[entity2] = connections.get(entity2, 0) + 1
    
    # Find most connected taxon
    most_connected = max(connections.items(), key=lambda x: x[1]) if connections else None
    
    return {
        "total_relationships": len(relationships),
        "unique_taxa": len(connections),
        "relationship_types": list(relationship_types),
        "most_connected_taxon": {
            "name": most_connected[0],
            "connections": most_connected[1]
        } if most_connected else None
    }

def classify_organism_type(classification: Dict[str, str]) -> str:
    """Classify organism type based on taxonomic classification"""
    kingdom = classification.get("kingdom", "").lower()
    
    if "animalia" in kingdom or "animal" in kingdom:
        return "animal"
    elif "plantae" in kingdom or "plant" in kingdom:
        return "plant"
    elif "fungi" in kingdom or "fungus" in kingdom:
        return "fungus"
    elif "bacteria" in kingdom:
        return "bacterium"
    elif "archaea" in kingdom:
        return "archaeon"
    elif "protist" in kingdom or "protista" in kingdom:
        return "protist"
    elif "virus" in kingdom or "viral" in kingdom:
        return "virus"
    else:
        return "unknown"

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

def parse_conservation_status(status: str) -> Dict[str, str]:
    """Parse conservation status and return structured data"""
    if not status:
        return {"status": "unknown", "category": "unknown"}
    
    status_lower = status.lower()
    
    # IUCN Red List categories
    if "extinct" in status_lower:
        if "wild" in status_lower:
            return {"status": "Extinct in the Wild", "category": "critical"}
        else:
            return {"status": "Extinct", "category": "extinct"}
    elif "critically endangered" in status_lower:
        return {"status": "Critically Endangered", "category": "critical"}
    elif "endangered" in status_lower:
        return {"status": "Endangered", "category": "threatened"}
    elif "vulnerable" in status_lower:
        return {"status": "Vulnerable", "category": "threatened"}
    elif "near threatened" in status_lower:
        return {"status": "Near Threatened", "category": "concern"}
    elif "least concern" in status_lower:
        return {"status": "Least Concern", "category": "stable"}
    else:
        return {"status": status, "category": "unknown"}
