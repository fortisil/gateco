"""Shared schema primitives used across all route modules."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata matching FE contract."""

    page: int
    per_page: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response envelope."""

    data: list[T]  # type: ignore[valid-type]
    meta: dict


class PaginationParams(BaseModel):
    """Standard list query parameters."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


def paginate_meta(page: int, per_page: int, total: int) -> dict:
    """Build the meta.pagination dict for a paginated response."""
    total_pages = max(1, (total + per_page - 1) // per_page)
    return {
        "pagination": PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ).model_dump()
    }


# ── Invoice status mapping (D2) ──

_INVOICE_STATUS_MAP = {
    "draft": "pending",
    "open": "pending",
    "paid": "paid",
    "void": "failed",
    "uncollectible": "failed",
}


def serialize_invoice_status(be_status: str) -> str:
    """Map backend invoice status to FE-expected value (D2)."""
    return _INVOICE_STATUS_MAP.get(be_status, be_status)


# Secret field sentinel — returned on read; FE shows "already set" placeholder
SECRET_REDACTED = None
