"""Tests for credential encryption – secrets must never be stored in plaintext."""

import pytest
from cryptography.fernet import Fernet

from aigateway.apps.providers.models import OrgProviderCredential


@pytest.mark.django_db
class TestCredentialEncryption:
    def test_set_and_get_secret(self, credential):
        """Credential round-trips correctly through encrypt/decrypt."""
        assert credential.get_secret() == "sk-test-key-12345678"

    def test_encrypted_secret_is_not_plaintext(self, credential):
        """The stored bytes must not contain the plaintext key."""
        raw = bytes(credential.encrypted_secret)
        assert b"sk-test-key-12345678" not in raw

    def test_secret_last4_stored(self, credential):
        """Last 4 chars of the key are stored for display."""
        assert credential.secret_last4 == "5678"

    def test_different_keys_produce_different_ciphertext(self, org, provider, settings):
        """Two credentials with different keys produce different ciphertext."""
        cred1 = OrgProviderCredential(
            organization=org, provider=provider, mode="BYO", encrypted_secret=b""
        )
        cred1.set_secret("key-aaaa-1111")

        cred2 = OrgProviderCredential(
            organization=org, provider=provider, mode="BYO", encrypted_secret=b""
        )
        cred2.set_secret("key-bbbb-2222")

        assert bytes(cred1.encrypted_secret) != bytes(cred2.encrypted_secret)

    def test_missing_encryption_key_raises(self, settings, org, provider):
        """If ENCRYPTION_KEY is unset, encryption raises ValueError."""
        settings.ENCRYPTION_KEY = ""
        cred = OrgProviderCredential(
            organization=org, provider=provider, mode="BYO", encrypted_secret=b""
        )
        with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
            cred.set_secret("some-key")
