import os
from typing import Any

import jwt
from jwt import InvalidTokenError


JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_REQUIRED = os.getenv("JWT_REQUIRED", "false").lower() == "true"


class AuthError(Exception):
    pass


def decode_bearer_token(auth_header: str | None) -> dict[str, Any]:
    if not auth_header:
        if JWT_REQUIRED:
            raise AuthError("missing_authorization_header")
        return {}

    if not auth_header.lower().startswith("bearer "):
        raise AuthError("invalid_authorization_scheme")

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise AuthError("empty_bearer_token")

    if not JWT_SECRET:
        raise AuthError("jwt_secret_not_configured")

    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return claims if isinstance(claims, dict) else {}
    except InvalidTokenError as exc:
        raise AuthError(f"invalid_token:{exc}") from exc


def merge_request_with_claims(payload: dict[str, Any], claims: dict[str, Any]) -> dict[str, Any]:
    # Trust claims first for identity and tenant boundaries.
    merged = dict(payload)

    claim_map = {
        "sub": "user_id",
        "user_id": "user_id",
        "role": "role",
        "tenant_id": "tenant_id",
        "purpose_of_use": "purpose_of_use",
    }

    for src, dst in claim_map.items():
        if claims.get(src) is not None:
            merged[dst] = claims[src]

    if isinstance(claims.get("attributes"), dict):
        merged["attributes"] = {**merged.get("attributes", {}), **claims["attributes"]}

    if isinstance(claims.get("context"), dict):
        merged["context"] = {**merged.get("context", {}), **claims["context"]}

    if isinstance(claims.get("patient_context"), dict):
        merged["patient_context"] = {**merged.get("patient_context", {}), **claims["patient_context"]}

    return merged
