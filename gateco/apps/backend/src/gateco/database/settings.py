"""
Database settings.

Reads DATABASE_URL from environment with mode detection.
"""

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Database configuration loaded from environment.

    Attributes:
        database_url: PostgreSQL connection string.
        db_vector_required: Whether pgvector extension is needed.
    """
    database_url: str = ""
    db_vector_required: bool = True

    @property
    def is_configured(self) -> bool:
        """Check if a database URL has been provided."""
        return bool(self.database_url)

    @property
    def is_local_docker(self) -> bool:
        """Detect if using local Docker PostgreSQL."""
        return "localhost" in self.database_url or "postgres:" in self.database_url

    class Config:
        env_file = ".env"
        extra = "ignore"


db_settings = DatabaseSettings()
