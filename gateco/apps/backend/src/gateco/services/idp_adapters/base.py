"""Base types for IDP sync adapters."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class SyncedPrincipal:
    """A principal fetched from an external identity provider."""

    external_id: str
    display_name: str
    email: str | None = None
    groups: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)


@dataclass
class SyncedGroup:
    """A group fetched from an external identity provider."""

    external_id: str
    name: str
    member_count: int = 0


@dataclass
class SyncResult:
    """Result of syncing from an external identity provider."""

    principals: list[SyncedPrincipal] = field(default_factory=list)
    groups: list[SyncedGroup] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BaseIDPAdapter(abc.ABC):
    """Abstract base for IDP sync adapters."""

    def __init__(self, config: dict) -> None:
        self.config = config

    @abc.abstractmethod
    async def sync(self) -> SyncResult:
        """Fetch users and groups from the provider. Returns SyncResult."""
        ...
