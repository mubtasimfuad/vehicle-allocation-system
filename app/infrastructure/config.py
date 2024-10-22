from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    ENV: str = "dev"  # Default to dev if not specified
    MONGO_URI: str
    REDIS_HOST: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    class Config:
        # Dynamically load the correct .env file based on the ENV variable
        print(f"Loading environment settings from {os.getenv('ENV')}")
        env_file = ".env.dev" if os.getenv("ENV") == "dev" else ".env.prod"

settings = Settings()
