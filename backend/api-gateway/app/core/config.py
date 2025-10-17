from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "change_this_secret_in_prod"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
