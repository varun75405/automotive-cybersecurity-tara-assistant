"""
Central configuration for the Automotive TARA AI Assistant.
Loaded from environment variables / .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()

# Load .env file if present
load_dotenv(PROJECT_ROOT / ".env")

class Settings:
    """Application settings with environment variable overrides."""

    def __init__(self):
        # --- LLM ---
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "openai" | "local" | "demo"
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.local_llm_url: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
        self.local_llm_model: str = os.getenv("LOCAL_LLM_MODEL", "llama3.1:8b")

        # --- Embeddings ---
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

        # --- ChromaDB ---
        self.chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "data" / "chroma_db"))

        # --- SQLite ---
        self.sqlite_db_path: str = os.getenv("SQLITE_DB_PATH", str(PROJECT_ROOT / "data" / "sqlite" / "tara.db"))

        # --- Export ---
        self.export_dir: str = os.getenv("EXPORT_DIR", str(PROJECT_ROOT / "data" / "exports"))

        # --- Application ---
        self.project_name: str = "Automotive TARA AI Assistant"
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
        self.backend_port: int = int(os.getenv("BACKEND_PORT", 8000))
        self.streamlit_port: int = int(os.getenv("STREAMLIT_PORT", 8501))

        # --- Auth ---
        self.auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
        self.auth_username: str = os.getenv("AUTH_USERNAME", "admin")
        self.auth_password: str = os.getenv("AUTH_PASSWORD", "tara_demo_2024")

        # --- Chunking ---
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", 512))
        self.chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", 64))

        # --- Ingestion ---
        self.max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", 50))

        # --- Retrieval ---
        self.retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", 5))

    def ensure_directories(self):
        """Create required data directories."""
        for dir_path in [self.chroma_persist_dir,
                         os.path.dirname(self.sqlite_db_path),
                         self.export_dir]:
            os.makedirs(dir_path, exist_ok=True)

_settings_instance = None

def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
