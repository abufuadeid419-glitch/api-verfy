"""Tests for the external Convex-hosted auth API (OTP + bearer-token /auth/me).

These tests target the deployed Convex HTTP router — NOT the local FastAPI stub.
"""
import pytest


# ---------- OTP request validation ----------

class TestOtpRequestValidation:
    def test_invalid_phone_returns_400_arabic(self, api_client, base_url):
        r = api_client.post(f"{base_url}/auth/otp/request", json={"phone": "123"})
        assert r.status_code == 400, r.text
        detail = (r.json() or {}).get("detail", "")
        # Expect: 'أدخل رقم هاتف صحيح مع رمز الدولة'
        assert "أدخل رقم هاتف صحيح" in detail or "رمز الدولة" in detail, detail


# ---------- OTP request Bird WhatsApp fallback failure (primary bug) ----------

class TestOtpRequestBirdFailure:
    """For a Syria number Bird SMS is disabled (E12020) and WhatsApp is unpriced.

    The backend fix polls WhatsApp status for several seconds and must surface a
    precise Arabic error mentioning WhatsApp and Bird, NOT return {ok:true}.
    """

    def test_syria_phone_returns_400_with_whatsapp_bird_arabic(self, api_client, base_url):
        # NOTE: this call can take ~8s because the backend polls Bird status.
        r = api_client.post(
            f"{base_url}/auth/otp/request",
            json={"phone": "+963984644375"},
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400 but got {r.status_code}: {r.text}"
        body = r.json() or {}
        # Should NOT be the silent success shape
        assert body.get("ok") is not True, body
        assert body.get("channel") is None, body
        detail = body.get("detail", "")
        assert isinstance(detail, str) and detail, body
        # Arabic error mentions WhatsApp AND Bird
        assert "واتساب" in detail, detail
        assert "Bird" in detail, detail


# ---------- OTP verify guard ----------

class TestOtpVerifyGuard:
    def test_verify_without_prior_request_returns_arabic_error(self, api_client, base_url):
        r = api_client.post(
            f"{base_url}/auth/otp/verify",
            json={"phone": "+963900000009", "code": "000000"},
        )
        assert r.status_code >= 400, r.text
        body = r.json() or {}
        detail = body.get("detail", "")
        assert isinstance(detail, str) and detail, body
        # Must be Arabic (contains at least one Arabic letter)
        assert any("\u0600" <= ch <= "\u06FF" for ch in detail), detail


# ---------- Seeded bearer tokens still authenticate ----------

class TestSeededBearerTokens:
    def _me(self, api_client, base_url, token):
        return api_client.get(
            f"{base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_owner_token_returns_owner_and_org_test_1(self, api_client, base_url):
        r = self._me(api_client, base_url, "test_token_owner")
        assert r.status_code == 200, r.text
        u = r.json()
        assert u.get("role") == "OWNER", u
        assert u.get("org_id") == "org_test_1", u

    def test_dev_token_returns_developer(self, api_client, base_url):
        r = self._me(api_client, base_url, "test_token_dev")
        assert r.status_code == 200, r.text
        u = r.json()
        assert u.get("role") == "DEVELOPER", u

    def test_missing_token_returns_401(self, api_client, base_url):
        r = api_client.get(f"{base_url}/auth/me")
        assert r.status_code == 401, r.text

    def test_invalid_token_returns_401(self, api_client, base_url):
        r = self._me(api_client, base_url, "not_a_real_token_xyz")
        assert r.status_code == 401, r.text
