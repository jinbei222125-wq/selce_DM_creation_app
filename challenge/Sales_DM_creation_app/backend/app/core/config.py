from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./insight_dm.db"
    )
    
    # App Settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    app_name: str = "Insight DM Master API"
    version: str = "1.0.0"
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # LangChain Settings
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.4
    tavily_max_results: int = 8
    tavily_search_depth: str = "advanced"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
