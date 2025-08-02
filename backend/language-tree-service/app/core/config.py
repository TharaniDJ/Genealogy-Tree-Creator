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
    SERVICE_NAME: str = "Language Tree Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = int(os.getenv("PORT", "8001"))
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    
    # WebSocket settings
    WEBSOCKET_TIMEOUT: int = 300  # 5 minutes
    MAX_CONNECTIONS: int = 100
    
    # Rate limiting
    MAX_DEPTH: int = 5
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # Caching
    CACHE_TTL: int = 3600  # 1 hour
    
    def __init__(self):
        """Initialize settings from environment variables"""
        pass

# Global settings instance
settings = Settings()
