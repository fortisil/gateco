"""PATCH merge utility with secret-aware handling."""


def apply_patch(existing: dict, patch: dict, secret_fields: list[str] | None = None) -> dict:
    """Merge PATCH body into existing data with secret-aware handling.

    - Regular fields: overwritten by patch value
    - Secret fields: empty string or missing → keep existing encrypted value
    - Secret fields: non-empty new value → replace (caller must encrypt)
    """
    secret_fields = secret_fields or []
    result = dict(existing)

    for key, value in patch.items():
        if key in secret_fields:
            if value is not None and value != "":
                result[key] = value
            # else: keep existing
        else:
            result[key] = value

    return result
