import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # API URLs
    WIKIPEDIA_API: str = "https://en.wikipedia.org/w/api.php"
    WIKIDATA_API: str = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
    SPARQL_API: str = "https://query.wikidata.org/sparql"
    WIKIDATA_QUERY_API: str = "https://www.wikidata.org/w/api.php"
    
    # Service configuration
    SERVICE_NAME: str = "Species Tree Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = int(os.getenv("PORT", "8002"))
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    
    # WebSocket settings
    WEBSOCKET_TIMEOUT: int = 300  # 5 minutes
    MAX_CONNECTIONS: int = 100
    
    # Rate limiting
    MAX_DEPTH: int = 6  # Taxonomic hierarchy can be deeper
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # Caching
    CACHE_TTL: int = 3600  # 1 hour
    
    # Taxonomic properties (Wikidata)
    TAXONOMIC_PROPERTIES = {
        "P171": "parent_taxon",        # Parent taxon
        "P105": "taxonomic_rank",      # Taxonomic rank
        "P225": "scientific_name",     # Scientific name
        "P1843": "common_name",        # Common name
        "P141": "conservation_status", # Conservation status
        "P183": "endemic_to",          # Endemic to
        "P2295": "habitat",            # Habitat
        "P2043": "length",             # Length
        "P2044": "height",             # Height
        "P2067": "mass",               # Mass
        "P2048": "height",             # Height
        "P18": "image",                # Image
        "P279": "subclass_of",         # Subclass of
        "P361": "part_of",             # Part of
    }
    
    # Taxonomic ranks
    TAXONOMIC_RANKS = {
        "Q36732": "kingdom",
        "Q38348": "phylum", 
        "Q5284": "class",
        "Q36602": "order",
        "Q35409": "family",
        "Q34740": "genus",
        "Q7432": "species",
        "Q68947": "subspecies",
        "Q3504061": "superorder",
        "Q2136103": "suborder",
        "Q164150": "infraorder",
        "Q2752679": "superfamily",
        "Q164280": "subfamily",
        "Q767728": "tribe",
        "Q3965313": "subtribe"
    }
    
    def __init__(self):
        """Initialize settings from environment variables"""
        pass

# Global settings instance
settings = Settings()
