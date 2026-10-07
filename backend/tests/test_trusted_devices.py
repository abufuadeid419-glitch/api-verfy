"""Tests for the Trusted Devices feature on the external Convex HTTP API.

Endpoints covered:
  POST  /api/auth/touch           — stamp/slide current session (trusted device)
  GET   /api/auth/sessions        — list user's trusted devices (no raw tokens)
  DELETE /api/auth/sessions/:id   — revoke a trusted device (idempotent)
  GET   /api/auth/me              — bearer token still authenticates
"""
import pytest


OWNER = "test_token_owner"
DEV = "test_token_dev"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- touch + list ----------

class TestTouchAndList:
    def test_touch_returns_ok(self, api_client, base_url):
        r = api_client.post(
            f"{base_url}/auth/touch",
            json={"device": "Pixel 8 (اختبار)", "platform": "android"},
            headers=_auth(OWNER),
            timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body == {"ok": True}, body

    def test_list_sessions_shape_and_current_flag(self, api_client, base_url):
        # Make sure a touch has happened at least once for this token
        api_client.post(
            f"{base_url}/auth/touch",
            json={"device": "Pixel 8 (اختبار)", "platform": "android"},
            headers=_auth(OWNER),
            timeout=30,
        )
        r = api_client.get(f"{base_url}/auth/sessions", headers=_auth(OWNER), timeout=30)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list) and len(rows) >= 1, rows

        # Required keys on every row
        required = {"device_id", "device", "platform", "last_seen_at", "current"}
        for row in rows:
            missing = required - set(row.keys())
            assert not missing, f"missing keys {missing} in {row}"
            # Raw tokens must NEVER be exposed in the API response
            assert "session_token" not in row, row
            assert "token" not in row, row

        # Exactly one row is the current session
        currents = [r for r in rows if r.get("current") is True]
        assert len(currents) == 1, currents

        # The current session reflects the just-stamped device label
        assert "اختبار" in (currents[0].get("device") or ""), currents[0]


# ---------- revoke guard ----------

class TestRevokeGuard:
    def test_revoke_nonexistent_is_idempotent_and_preserves_current(self, api_client, base_url):
        # Snapshot current session count
        r0 = api_client.get(f"{base_url}/auth/sessions", headers=_auth(OWNER), timeout=30)
        assert r0.status_code == 200
        before = r0.json()
        assert any(x.get("current") for x in before)

        # Revoke a bogus device_id — should be a no-op success
        r1 = api_client.delete(
            f"{base_url}/auth/sessions/nonexistent-id-xyz",
            headers=_auth(OWNER),
            timeout=30,
        )
        assert r1.status_code == 200, r1.text
        assert r1.json() == {"ok": True}, r1.text

        # Current session must still authenticate
        me = api_client.get(f"{base_url}/auth/me", headers=_auth(OWNER), timeout=30)
        assert me.status_code == 200, me.text
        assert (me.json() or {}).get("role") == "OWNER"


# ---------- /auth/me still works ----------

class TestAuthMe:
    def test_owner(self, api_client, base_url):
        r = api_client.get(f"{base_url}/auth/me", headers=_auth(OWNER), timeout=30)
        assert r.status_code == 200
        assert r.json().get("role") == "OWNER"

    def test_developer(self, api_client, base_url):
        r = api_client.get(f"{base_url}/auth/me", headers=_auth(DEV), timeout=30)
        assert r.status_code == 200
        assert r.json().get("role") == "DEVELOPER"

    def test_missing_token(self, api_client, base_url):
        r = api_client.get(f"{base_url}/auth/me", timeout=30)
        assert r.status_code == 401

    def test_invalid_token(self, api_client, base_url):
        r = api_client.get(
            f"{base_url}/auth/me",
            headers={"Authorization": "Bearer not_a_real_token_xyz"},
            timeout=30,
        )
        assert r.status_code == 401
