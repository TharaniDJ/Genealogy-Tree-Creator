from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "change_this_secret_in_prod"
    ALGORITHM: str = "HS256"
    
    # Explicit backend and frontend URLs (read from .env or use defaults)
    FRONTEND_URL: str = ""
    FAMILY_SERVICE_URL: str = ""
    LANGUAGE_SERVICE_URL: str = ""
    SPECIES_SERVICE_URL: str = ""
    USER_SERVICE_URL: str = ""

    FAMILY_WS_URL: str = ""
    LANGUAGE_WS_URL: str = ""
    SPECIES_WS_URL: str = ""

    # pydantic v2 style config: read .env but ignore extra keys so other services'
    # env vars don't raise ValidationError.
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
