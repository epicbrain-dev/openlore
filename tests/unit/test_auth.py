"""Unit tests for enterprise RBAC and HMAC-SHA256 bearer token authentication."""

from __future__ import annotations

import time
import unittest

from openlore.server.auth import (
    AuthToken,
    Permission,
    Role,
    TokenService,
    authenticate_request,
)


class TestAuthService(unittest.TestCase):
    def test_token_creation_and_verification(self) -> None:
        token = TokenService.create_token(
            sub="lead_td",
            role=Role.TD,
            expires_in_seconds=3600,
            secret="test-secret-key-123",
        )
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split(".")), 3)

        decoded = TokenService.verify_token(token, secret="test-secret-key-123")
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.sub, "lead_td")
        self.assertEqual(decoded.role, Role.TD)
        self.assertTrue(decoded.has_permission(Permission.PROMOTE_STAGE))
        self.assertTrue(decoded.has_permission(Permission.EDIT_STAGE))
        self.assertFalse(decoded.has_permission(Permission.MANAGE_SYSTEM))

    def test_tampered_token_rejected(self) -> None:
        token = TokenService.create_token(sub="artist_user", role=Role.ARTIST, secret="secret-A")
        # Verify with wrong secret
        self.assertIsNone(TokenService.verify_token(token, secret="secret-B"))

        # Tamper payload
        parts = token.split(".")
        tampered = f"{parts[0]}.eyJhZG1pbiI6IHRydWV9.{parts[2]}"
        self.assertIsNone(TokenService.verify_token(tampered, secret="secret-A"))

    def test_expired_token_rejected(self) -> None:
        token = TokenService.create_token(
            sub="old_user",
            role=Role.VIEWER,
            expires_in_seconds=-10,  # Already expired
            secret="secret-key",
        )
        self.assertIsNone(TokenService.verify_token(token, secret="secret-key"))

    def test_role_hierarchy_permissions(self) -> None:
        admin_token = TokenService.create_token(sub="boss", role=Role.ADMIN)
        admin = TokenService.verify_token(admin_token)
        self.assertTrue(admin.has_permission(Permission.MANAGE_SYSTEM))
        self.assertTrue(admin.has_permission(Permission.PROMOTE_STAGE))

        artist_token = TokenService.create_token(sub="sculptor", role=Role.ARTIST)
        artist = TokenService.verify_token(artist_token)
        self.assertTrue(artist.has_permission(Permission.EDIT_STAGE))
        self.assertFalse(artist.has_permission(Permission.PROMOTE_STAGE))
        self.assertFalse(artist.has_permission(Permission.MANAGE_SYSTEM))

        partner_token = TokenService.create_token(sub="vendor", role=Role.PARTNER)
        partner = TokenService.verify_token(partner_token)
        self.assertTrue(partner.has_permission(Permission.VIEW_STAGE))
        self.assertFalse(partner.has_permission(Permission.EDIT_STAGE))

    def test_authenticate_request_helper(self) -> None:
        token_str = TokenService.create_token(sub="td_alex", role=Role.TD, secret="test-secret")
        headers = {"Authorization": f"Bearer {token_str}"}

        # Passing correct permission with enforced auth
        auth_ok, token, err = authenticate_request(
            headers=headers,
            query_params={},
            required_permission=Permission.PROMOTE_STAGE,
            secret="test-secret",
            enforce_auth=True,
        )
        self.assertTrue(auth_ok)
        self.assertIsNotNone(token)
        self.assertEqual(token.sub, "td_alex")

        # Query param fallback (?token=...) with enforced auth
        auth_ok_qp, token_qp, _ = authenticate_request(
            headers={},
            query_params={"token": [token_str]},
            secret="test-secret",
            enforce_auth=True,
        )
        self.assertTrue(auth_ok_qp)
        self.assertEqual(token_qp.sub, "td_alex")


if __name__ == "__main__":
    unittest.main()
