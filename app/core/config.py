from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AI-Powered Customer Support & Ticket Intelligence"
    app_env: str = "development"
    api_v1_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://ticket_user:ticket_password@localhost:5432/ticket_intelligence"
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    llm_timeout_seconds: float = 45.0
    llm_max_retries: int = 1
    max_query_length: int = 5000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
