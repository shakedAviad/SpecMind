from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "jls_chunks"

    jls_pdf_path: str = "jls25.pdf"
