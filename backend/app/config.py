import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LOG_LEVEL: str = "info"
    UPLOAD_DIR: str = "uploads"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Embeddings and FAISS config
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "faiss_index"
    
    # Default file path
    DEFAULT_EXCEL_PATH: str = "synthetic_skill_dataset.xlsx"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
