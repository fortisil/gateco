"""AppSettings model.

Key-value configuration storage for runtime settings.
Migrated from legacy models.py for compatibility with models package.
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.models.base import Base, TimestampMixin


class AppSettings(Base, TimestampMixin):
    """Key-value configuration storage.

    Used for runtime settings that persist across restarts.
    """

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<AppSettings(key={self.key!r})>"


__all__ = ["AppSettings"]
