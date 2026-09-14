"""Enterprise Role-Based Access Control (RBAC) and HMAC token authentication."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

DEFAULT_SECRET_KEY = os.getenv("OPENLORE_AUTH_SECRET", "openlore-studio-master-hmac-secret-2026")
AUTH_ENABLED = os.getenv("OPENLORE_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")


class Role(str, Enum):
    """User roles within the OpenLore studio ecosystem."""

    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    TD = "td"
    ARTIST = "artist"
    PARTNER = "partner"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular capabilities evaluated across OpenLore subsystems."""

    VIEW_STAGE = "view_stage"
    EDIT_STAGE = "edit_stage"
    PROMOTE_STAGE = "promote_stage"
    DISPATCH_JOB = "dispatch_job"
    MANAGE_SYSTEM = "manage_system"


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.VIEW_STAGE,
        Permission.EDIT_STAGE,
        Permission.PROMOTE_STAGE,
        Permission.DISPATCH_JOB,
        Permission.MANAGE_SYSTEM,
    },
    Role.SUPERVISOR: {
        Permission.VIEW_STAGE,
        Permission.EDIT_STAGE,
        Permission.PROMOTE_STAGE,
        Permission.DISPATCH_JOB,
    },
    Role.TD: {
        Permission.VIEW_STAGE,
        Permission.EDIT_STAGE,
        Permission.PROMOTE_STAGE,
        Permission.DISPATCH_JOB,
    },
    Role.ARTIST: {
        Permission.VIEW_STAGE,
        Permission.EDIT_STAGE,
        Permission.DISPATCH_JOB,
    },
    Role.PARTNER: {
        Permission.VIEW_STAGE,
    },
    Role.VIEWER: {
        Permission.VIEW_STAGE,
    },
}


@dataclass
class AuthToken:
    """Decoded and verified OpenLore Bearer Token."""

    sub: str  # Subject / Username
    role: Role
    exp: float
    permissions: List[str] = field(default_factory=list)

    def has_permission(self, permission: Permission) -> bool:
        """Check if token possesses specified capability."""
        return permission.value in self.permissions or permission in ROLE_PERMISSIONS.get(self.role, set())

    def is_expired(self) -> bool:
        """Check if current timestamp exceeds expiration."""
        return time.time() > self.exp


class TokenService:
    """Standard-library HMAC-SHA256 Token Generator and Verifier."""

    @staticmethod
    def _b64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64_decode(data: str) -> bytes:
        padding = "=" * ((4 - len(data) % 4) % 4)
        return base64.urlsafe_b64decode(data + padding)

    @classmethod
    def create_token(
        cls,
        sub: str,
        role: Role = Role.ARTIST,
        expires_in_seconds: int = 86400 * 30,  # 30 days default
        secret: str = DEFAULT_SECRET_KEY,
    ) -> str:
        """Generate an HMAC-SHA256 signed bearer token."""
        header = {"alg": "HS256", "typ": "OLJWT"}
        exp = time.time() + expires_in_seconds
        perms = [p.value for p in ROLE_PERMISSIONS.get(role, set())]
        payload = {
            "sub": sub,
            "role": role.value,
            "exp": exp,
            "perms": perms,
        }

        hdr_b64 = cls._b64_encode(json.dumps(header).encode("utf-8"))
        pay_b64 = cls._b64_encode(json.dumps(payload).encode("utf-8"))
        msg = f"{hdr_b64}.{pay_b64}".encode("utf-8")

        sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
        sig_b64 = cls._b64_encode(sig)

        return f"{hdr_b64}.{pay_b64}.{sig_b64}"

    @classmethod
    def verify_token(
        cls,
        token: str,
        secret: str = DEFAULT_SECRET_KEY,
    ) -> Optional[AuthToken]:
        """Verify HMAC signature, parse claims, and check expiration."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            hdr_b64, pay_b64, sig_b64 = parts
            msg = f"{hdr_b64}.{pay_b64}".encode("utf-8")
            expected_sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
            actual_sig = cls._b64_decode(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload = json.loads(cls._b64_decode(pay_b64).decode("utf-8"))
            auth_token = AuthToken(
                sub=payload["sub"],
                role=Role(payload["role"]),
                exp=payload["exp"],
                permissions=payload.get("perms", []),
            )

            if auth_token.is_expired():
                return None

            return auth_token
        except Exception:
            return None


def authenticate_request(
    headers: Dict[str, str],
    query_params: Dict[str, Any],
    required_permission: Optional[Permission] = None,
    secret: str = DEFAULT_SECRET_KEY,
    enforce_auth: Optional[bool] = None,
) -> Tuple[bool, Optional[AuthToken], Optional[str]]:
    """Evaluate authorization for an incoming HTTP or WebSocket request.
    
    Returns: (is_authorized, auth_token, error_message)
    """
    is_enforced = AUTH_ENABLED if enforce_auth is None else enforce_auth
    if not is_enforced:
        # Dev / Offline mode: grant administrative bypass
        dev_token = AuthToken(
            sub="dev-studio-user",
            role=Role.ADMIN,
            exp=time.time() + 86400,
            permissions=[p.value for p in Permission],
        )
        return True, dev_token, None

    raw_token = None
    # 1. Inspect Authorization Header: "Bearer <token>"
    auth_header = headers.get("Authorization") or headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        raw_token = auth_header[7:].strip()

    # 2. Inspect query parameter: ?token=<token> (useful for WebSockets)
    if not raw_token:
        raw_token = query_params.get("token")
        if isinstance(raw_token, list) and raw_token:
            raw_token = raw_token[0]

    if not raw_token:
        return False, None, "Missing Authorization Bearer token."

    token = TokenService.verify_token(raw_token, secret=secret)
    if not token:
        return False, None, "Invalid or expired authorization token."

    if required_permission and not token.has_permission(required_permission):
        return False, token, f"Forbidden: Role '{token.role.value}' lacks permission '{required_permission.value}'."

    return True, token, None
