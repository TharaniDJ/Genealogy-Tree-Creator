from pydantic_settings import BaseSettings  # ← CHANGED FROM pydantic
#from pydantic import BaseSettings

class Settings(BaseSettings):
    WIKIPEDIA_API: str = "https://en.wikipedia.org/w/api.php"
    WIKIDATA_API: str = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
    WEBSOCKET_URL: str = "ws://localhost:8000/ws"
    GEMINI_API_KEY: str 
    class Config:
        env_file = ".env"

settings = Settings()