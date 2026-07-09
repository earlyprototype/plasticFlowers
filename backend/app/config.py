"""Centralised runtime configuration for the FastAPI backend.

This module intentionally lives outside the service layer so that both API
routers and services can import a single `get_settings()` helper without
creating circular dependencies. Values map 1:1 with the Gate 3 plan.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the env file to the repo root (this file is backend/app/config.py)
# so settings load identically regardless of the current working directory.
_REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or `.env` files."""

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT_ENV_FILE, env_file_encoding="utf-8"
    )

    neo4j_uri: str = Field(
        "neo4j://127.0.0.1:7687",
        description="Bolt/Neo4j connection URI (bolt, neo4j, or neo4j+s). Use 127.0.0.1 on Windows to avoid IPv6 fallback delays.",
    )
    neo4j_username: str = Field("neo4j", description="Neo4j authentication username.")
    neo4j_password: SecretStr = Field(
        SecretStr("plasticflower"),
        description="Neo4j authentication password (store securely outside Git).",
    )
    neo4j_max_connection_pool_size: int = Field(
        10, ge=1, description="Upper bound for the async driver's pooled connections."
    )
    neo4j_max_connection_lifetime: int = Field(
        3600,
        ge=60,
        description="Seconds before pooled connections recycle to avoid stale sessions.",
    )
    gemini_api_key: SecretStr = Field(
        SecretStr(""),
        description="API key for Google Generative AI (environment: GEMINI_API_KEY).",
    )
    vertex_project_id: str = Field(
        "",
        description="Google Cloud Project ID for Vertex AI (optional).",
    )
    vertex_location: str = Field(
        "us-central1",
        description="Google Cloud Region for Vertex AI (e.g., us-central1).",
    )
    gemini_model: str = Field(
        "gemini-2.5-flash",
        description="Default Gemini model (deprecated: use gemini_model_builder/gardener).",
    )
    gemini_model_builder: str = Field(
        "gemini-2.5-flash",
        description="Model for Builder agent (high volume extraction).",
    )
    gemini_model_gardener: str = Field(
        "gemini-2.5-flash",
        description="Model for Gardener agent (using flash for higher rate limits on free tier).",
    )
    gemini_temperature: float = Field(
        0.2,
        ge=0.0,
        le=1.0,
        description="Controls randomness of LLM output (0 = deterministic, 1 = creative).",
    )
    gemini_top_p: float = Field(
        0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling limit for Gemini responses.",
    )
    gemini_max_output_tokens: int = Field(
        131072,
        ge=64,
        le=131072,
        description="Upper bound on tokens returned per Builder invocation.",
    )
    gemini_request_timeout: float = Field(
        90.0,
        ge=1.0,
        description="Seconds before a Gemini request is cancelled. 90s sufficient with thinking_budget=0.",
    )
    gemini_max_retries: int = Field(
        2,
        ge=0,
        le=5,
        description="Transient error retries for Gemini requests (exponential backoff).",
    )
    embedding_dimensions: int = Field(
        768,
        ge=1,
        description="Dimensions produced by the Google `text-embedding-004` model.",
    )
    embedding_model: str = Field(
        "models/text-embedding-004",
        description="Google embedding model used for vector similarity.",
    )
    embedding_cache_size: int = Field(
        512,
        ge=1,
        le=4096,
        description="Maximum memoised embeddings stored in-process (LRU).",
    )
    embedding_similarity_function: str = Field(
        "cosine",
        description="Neo4j vector similarity function (cosine/dotproduct/euclidean).",
    )
    similarity_threshold: float = Field(
        0.92,
        ge=0.0,
        le=1.0,
        description="Pre-Builder duplication threshold. Tuned via Phase B testing: 0.92 balances precision (avoids merging distinct concepts like Neo4j/MongoDB) with recall (catches AI/Artificial Intelligence). See ADR-008.",
    )
    similarity_top_k: int = Field(
        5,
        ge=1,
        le=50,
        description="Top-K candidates fetched from Neo4j vector index before threshold filtering.",
    )
    redis_url: str = Field(
        "redis://localhost:6379",
        description="Redis connection URL for event streams.",
    )
    gardener_debounce_seconds: float = Field(
        5.0,
        ge=0.0,
        le=300.0,
        description=(
            "Per-session Gardener coalescing window in seconds: after a run, the next "
            "run for that session is scheduled no sooner than this many seconds later; "
            "chunk events arriving inside the window coalesce into that one scheduled run."
        ),
    )
    builder_gardener_ratio: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of Builder runs before triggering one Gardener run. E.g., 5 = every 5 chunks processed.",
    )

    researcher_enabled: bool = Field(
        True,
        description=(
            "Enable automatic Researcher dispatch: the Gardener scheduler checks "
            "this before publishing research triggers. Manual research via "
            "POST /sessions/{id}/nodes/{node_id}/research is unaffected."
        ),
    )
    tavily_api_key: SecretStr = Field(
        SecretStr(""),
        description="API key for Tavily search (environment: TAVILY_API_KEY).",
    )
    tavily_mcp_url: str = Field(
        "https://mcp.tavily.com/mcp/",
        description="Tavily remote MCP server URL.",
    )
    similarity_check_enabled: bool = Field(
        True,
        description="Enable pre-creation similarity check in Builder. Set false to revert to GHOST-only mode (ADR-011).",
    )
    type_similarity_threshold: float = Field(
        0.80,
        ge=0.0,
        le=1.0,
        description="Embedding similarity threshold for type compatibility check (ADR-013).",
    )

    @field_validator("gemini_model_builder", "gemini_model_gardener")
    @classmethod
    def correct_preview_models(cls, v: str) -> str:
        """Auto-correct model names if environment variables use the short form."""
        if v == "gemini-3-flash":
            return "gemini-3-flash-preview"
        if v == "gemini-3-pro":
            return "gemini-3-pro-preview"
        return v

    @property
    def neo4j_auth(self) -> tuple[str, str]:
        """Return credentials in the tuple format expected by the Neo4j driver."""

        return (self.neo4j_username, self.neo4j_password.get_secret_value())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return memoised settings instance so repeated imports stay lightweight."""

    return Settings()
