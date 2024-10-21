from pydantic import BaseSettings


class Settings(BaseSettings):
    ENV: str = "dev"  # Default to development
    MONGO_URI: str
    REDIS_HOST: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    class Config:
        env_file = ".env"  # Pydantic will load from .env file by default for local dev


# Instantiate the settings
settings = Settings()
