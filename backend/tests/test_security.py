"""Unit tests for app.security (password hashing, JWT tokens)."""
import pytest

from app.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_hash_produces_different_salts(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # different salts
        assert verify_password("same", h1) is True
        assert verify_password("same", h2) is True

    def test_verify_invalid_hash(self):
        # Malformed hash should return False, not raise
        assert verify_password("anything", "not-a-valid-hash") is False


class TestJWT:
    def test_create_and_decode_admin(self):
        token = create_access_token(42, "admin")
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "admin"

    def test_create_and_decode_customer(self):
        token = create_access_token(99, "customer")
        payload = decode_token(token)
        assert payload["sub"] == "99"
        assert payload["type"] == "customer"

    def test_token_contains_exp(self):
        token = create_access_token(1)
        payload = decode_token(token)
        assert "exp" in payload

    def test_default_type_is_admin(self):
        token = create_access_token(1)
        payload = decode_token(token)
        assert payload["type"] == "admin"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(Exception):
            decode_token("not.a.valid.jwt")

    def test_subject_stored_as_string(self):
        token = create_access_token(123)
        payload = decode_token(token)
        assert isinstance(payload["sub"], str)
        assert payload["sub"] == "123"
