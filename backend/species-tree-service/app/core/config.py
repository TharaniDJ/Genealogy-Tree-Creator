"""
Core configuration for Species Tree Service
"""

import os
from typing import Optional

class Config:
    """Application configuration"""
    
    # Service settings
    SERVICE_NAME: str = "Species Tree Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API settings
    API_PREFIX: str = "/api/species"
    
    # External services
    WIKIDATA_ENDPOINT: str = "https://query.wikidata.org/sparql"
    WIKIPEDIA_BASE_URL: str = "https://en.wikipedia.org/wiki/"
    
    # Rate limiting
    WIKIPEDIA_REQUEST_DELAY: float = 1.0  # seconds between requests
    WIKIDATA_REQUEST_DELAY: float = 0.1   # seconds between requests
    REQUEST_TIMEOUT: int = 10             # seconds
    
    # Caching
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Global config instance
config = Config()