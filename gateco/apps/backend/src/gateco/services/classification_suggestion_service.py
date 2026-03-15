"""Classification suggestion service — rule-based MVP.

Suggests classifications for unmanaged vectors based on:
1. Payload inspection (inline metadata from vector payload)
2. Pattern matching (keyword rules on resource_key / vector_id)
3. Namespace analysis (connector-specific metadata)
"""

import logging
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import Classification, ResourceType, Sensitivity
from gateco.database.models.connector import Connector
from gateco.database.models.resource import GatedResource
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.exceptions import ValidationError
from gateco.schemas.connectors import CONNECTOR_SECRET_FIELDS
from gateco.schemas.suggestions import (
    ApplySuggestionsRequest,
    ApplySuggestionsResponse,
    ClassificationSuggestion,
    SuggestClassificationsRequest,
    SuggestClassificationsResponse,
)
from gateco.services.connector_adapters import list_vector_ids
from gateco.services.connector_service import _load
from gateco.services.retroactive_service import _apply_grouping
from gateco.utils.crypto import decrypt_config_secrets

logger = logging.getLogger(__name__)

# Rule-based classification rules: (keywords, classification, sensitivity, confidence)
CLASSIFICATION_RULES: list[tuple[list[str], str, str, float]] = [
    (["hr", "employee", "personnel", "payroll"], "confidential", "high", 0.8),
    (["finance", "revenue", "budget", "invoice"], "restricted", "critical", 0.8),
    (["legal", "contract", "compliance"], "restricted", "high", 0.75),
    (["public", "blog", "docs", "readme", "faq"], "public", "low", 0.9),
    (["internal", "wiki", "handbook", "onboarding"], "internal", "medium", 0.7),
    (["engineering", "code", "deploy", "infra"], "internal", "medium", 0.65),
]

VALID_CLASSIFICATIONS = {e.value for e in Classification}
VALID_SENSITIVITIES = {e.value for e in Sensitivity}


def _match_pattern_rules(resource_key: str) -> ClassificationSuggestion | None:
    """Apply keyword-based pattern matching to a resource key."""
    key_lower = resource_key.lower()
    best_match: tuple[str, str, float, str] | None = None

    for keywords, classification, sensitivity, confidence in CLASSIFICATION_RULES:
        for kw in keywords:
            if kw in key_lower:
                if best_match is None or confidence > best_match[2]:
                    best_match = (
                        classification,
                        sensitivity,
                        confidence,
                        f"Keyword '{kw}' matched in resource key",
                    )
                break

    if best_match:
        return ClassificationSuggestion(
            resource_key=resource_key,
            suggested_classification=best_match[0],
            suggested_sensitivity=best_match[1],
            confidence=best_match[2],
            reasoning=best_match[3],
        )
    return None


async def suggest_classifications(
    session: AsyncSession,
    org_id: UUID,
    connector_id: UUID,
    request: SuggestClassificationsRequest,
) -> SuggestClassificationsResponse:
    """Generate classification suggestions for a connector's vectors.

    Uses rule-based pattern matching on resource keys / vector IDs.
    """
    connector = await _load(session, org_id, connector_id)

    # Scan vector IDs
    secret_fields = CONNECTOR_SECRET_FIELDS.get(connector.type.value, [])
    decrypted_config = decrypt_config_secrets(connector.config or {}, secret_fields)
    search_config = connector.search_config or {}

    try:
        from gateco.services.connector_adapters import list_vector_ids

        all_vector_ids = await list_vector_ids(
            connector.type.value, decrypted_config, search_config, request.scan_limit,
        )
    except Exception as e:
        raise ValidationError(detail=f"Failed to scan vector IDs: {e}")

    scanned_count = len(all_vector_ids)
    if not all_vector_ids:
        return SuggestClassificationsResponse(
            status="success", scanned_vectors=0, suggestions=[],
        )

    # Apply grouping
    groups = _apply_grouping(
        all_vector_ids, request.grouping_strategy, request.grouping_pattern,
    )

    # Generate suggestions per group
    suggestions: list[ClassificationSuggestion] = []
    for resource_key, vector_ids in groups.items():
        suggestion = _match_pattern_rules(resource_key)
        if suggestion:
            suggestion.vector_ids = vector_ids[:request.sample_size]
        else:
            # No pattern match — return as unclassified suggestion
            suggestion = ClassificationSuggestion(
                resource_key=resource_key,
                vector_ids=vector_ids[:request.sample_size],
                confidence=0.0,
                reasoning="No pattern match — manual classification recommended",
            )
        suggestions.append(suggestion)

    return SuggestClassificationsResponse(
        status="success",
        scanned_vectors=scanned_count,
        suggestions=suggestions,
    )


async def apply_suggestions(
    session: AsyncSession,
    org_id: UUID,
    connector_id: UUID,
    request: ApplySuggestionsRequest,
) -> ApplySuggestionsResponse:
    """Apply approved classification suggestions by creating GatedResource + ResourceChunk records."""
    connector = await _load(session, org_id, connector_id)

    applied = 0
    resources_created = 0
    errors: list[dict] = []

    for suggestion in request.suggestions:
        try:
            # Check if resource already exists
            existing = await session.execute(
                select(GatedResource).where(
                    GatedResource.organization_id == org_id,
                    GatedResource.source_connector_id == connector_id,
                    GatedResource.external_resource_key == suggestion.resource_key,
                    GatedResource.deleted_at.is_(None),
                )
            )
            resource = existing.scalar_one_or_none()

            if resource is None:
                resource = GatedResource(
                    organization_id=org_id,
                    source_connector_id=connector_id,
                    external_resource_key=suggestion.resource_key,
                    type=ResourceType.file,
                    title=suggestion.resource_key,
                    content_url=f"suggestion://{suggestion.resource_key}",
                )
                resources_created += 1

            if suggestion.suggested_classification and suggestion.suggested_classification in VALID_CLASSIFICATIONS:
                resource.classification = Classification(suggestion.suggested_classification)
            if suggestion.suggested_sensitivity and suggestion.suggested_sensitivity in VALID_SENSITIVITIES:
                resource.sensitivity = Sensitivity(suggestion.suggested_sensitivity)
            if suggestion.suggested_domain:
                resource.domain = suggestion.suggested_domain

            session.add(resource)
            await session.flush()

            # Create chunks for vector IDs
            for i, vid in enumerate(suggestion.vector_ids):
                chunk_result = await session.execute(
                    select(ResourceChunk).where(
                        ResourceChunk.source_connector_id == connector_id,
                        ResourceChunk.vector_id == vid,
                    )
                )
                if chunk_result.scalar_one_or_none() is None:
                    chunk = ResourceChunk(
                        resource_id=resource.id,
                        source_connector_id=connector_id,
                        index=i,
                        vector_id=vid,
                    )
                    session.add(chunk)

            applied += 1
        except Exception as e:
            logger.error(
                "apply_suggestion_error resource_key=%s error=%s",
                suggestion.resource_key, str(e),
            )
            errors.append({
                "resource_key": suggestion.resource_key,
                "error": str(e),
            })

    await session.flush()

    status = "success" if not errors else "partial_success"
    return ApplySuggestionsResponse(
        status=status,
        applied=applied,
        resources_created=resources_created,
        errors=errors,
    )
