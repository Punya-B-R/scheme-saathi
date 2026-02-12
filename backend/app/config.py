"""
Configuration & environment variables for Scheme Saathi backend.
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (.env file)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # API Keys
    GEMINI_API_KEY: str = "placeholder"
    OPENAI_API_KEY: str = ""

    # Embedding (for ChromaDB vector search)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"

    # Chat LLM: when set, use OpenAI for chat (e.g. gpt-5.2-chat-latest); else Gemini
    OPENAI_CHAT_MODEL: str = "gpt-5.2-chat-latest"

    # Model Configuration (Gemini, used only when OPENAI_CHAT_MODEL is not used)
    GEMINI_MODEL: str = "gemini-3-pro-preview"

    # Application Settings
    APP_NAME: str = "Scheme Saathi"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database (PostgreSQL; required for auth and chat history)
    DATABASE_URL: str = ""

    # Data Paths
    SCHEMES_DATA_PATH: str = "data_f/all_schemes.json"
    CHROMA_DB_PATH: str = "chroma_db"

    # RAG Settings
    TOP_K_SCHEMES: int = 10  # Number of schemes to retrieve
    SIMILARITY_THRESHOLD: float = 0.3  # Minimum similarity score (0-1)

    SUPABASE_URL: str = ""
    # Legacy JWT secret (HS256); only needed if SUPABASE_URL is not set
    SUPABASE_JWT_SECRET: str = ""

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def get_schemes_path(self, base_dir: Path) -> Path:
        """Resolve schemes JSON path relative to backend root."""
        return base_dir / self.SCHEMES_DATA_PATH

    def get_chroma_path(self, base_dir: Path) -> Path:
        """Resolve ChromaDB persistence path."""
        return base_dir / self.CHROMA_DB_PATH


# Global settings instance (singleton)
settings = Settings()
