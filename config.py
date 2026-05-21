import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Manages application settings for LLM APIs."""
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
    gemini_model_name: str = "gemini-2.5-flash"
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY_HERE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
