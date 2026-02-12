"""Tests for API endpoints, API key management, and public pages."""

from decimal import Decimal

import pytest
from django.test import RequestFactory

from aigateway.apps.api.authentication import ApiKeyAuthentication
from aigateway.apps.billing.models import ApiKey, CreditLedgerEntry


@pytest.mark.django_db
class TestModelsListAPI:
    """GET /api/v1/models"""

    def test_empty_models_list(self, client):
        """Returns 200 with empty data when no models exist."""
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_models_list_with_data(self, client, provider_model):
        """Returns model list with correct format when models exist."""
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        model = data[0]
        assert model["id"] == "openai/gpt-4o-mini"
        assert model["name"] == "GPT-4o Mini"
        assert model["provider"] == "openai"

    def test_model_data_includes_expected_fields(self, client, provider_model):
        """Model data includes pricing, modality, context_length, supported_parameters."""
        response = client.get("/api/v1/models")
        model = response.json()["data"][0]
        assert "pricing" in model
        assert "prompt" in model["pricing"]
        assert "completion" in model["pricing"]
        assert "modality" in model
        assert "context_length" in model
        assert "supported_parameters" in model
        assert "is_free" in model


@pytest.mark.django_db
class TestModelDetailAPI:
    """GET /api/v1/models/{provider}/{model}"""

    def test_nonexistent_model_returns_404(self, client):
        """Returns 404 for non-existent model."""
        response = client.get("/api/v1/models/fake-provider/fake-model")
        assert response.status_code == 404

    def test_existing_model_returns_data(self, client, provider_model):
        """Returns model data for existing model."""
        response = client.get("/api/v1/models/openai/gpt-4o-mini")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "openai/gpt-4o-mini"
        assert data["name"] == "GPT-4o Mini"
        assert data["provider"] == "openai"


@pytest.mark.django_db
class TestApiKeyModel:
    """ApiKey.create_key and ApiKey.lookup"""

    def test_create_key_generates_correct_prefix(self, org):
        """ApiKey.create_key generates key with correct prefix."""
        instance, plaintext = ApiKey.create_key(organization=org)
        assert plaintext.startswith("sk-or-v1-")
        assert instance.prefix == plaintext[:8]

    def test_lookup_finds_key(self, org):
        """ApiKey.lookup finds key by plaintext."""
        instance, plaintext = ApiKey.create_key(organization=org)
        found = ApiKey.lookup(plaintext)
        assert found is not None
        assert found.pk == instance.pk

    def test_lookup_returns_none_for_invalid_key(self, db):
        """ApiKey.lookup returns None for invalid key."""
        result = ApiKey.lookup("sk-or-v1-0000000000000000000000000000000000000000000000000000000000000000")
        assert result is None

    def test_key_stored_hashed(self, org):
        """Key is stored hashed (plaintext not in hashed_key)."""
        instance, plaintext = ApiKey.create_key(organization=org)
        assert plaintext not in instance.hashed_key
        assert len(instance.hashed_key) == 64  # SHA-256 hex digest


@pytest.mark.django_db
class TestApiKeyAuthentication:
    """API key authentication via ApiKeyAuthentication class."""

    def test_valid_api_key_sets_org_context(self, org):
        """Request with valid API key sets org context."""
        _, plaintext = ApiKey.create_key(organization=org)
        factory = RequestFactory()
        request = factory.get("/api/v1/credits", HTTP_AUTHORIZATION=f"Bearer {plaintext}")
        auth = ApiKeyAuthentication()
        result = auth.authenticate(request)
        assert result is not None
        assert request.org == org

    def test_invalid_api_key_returns_error(self, client):
        """Request with invalid API key returns 401/403."""
        response = client.get(
            "/api/v1/credits",
            HTTP_AUTHORIZATION="Bearer sk-or-v1-0000000000000000000000000000000000000000000000000000000000000000",
        )
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestCreditsAPI:
    """GET /api/v1/credits"""

    def test_zero_balance_for_new_org(self, client, org):
        """Returns zero balance for new org."""
        response = client.get(
            "/api/v1/credits",
            HTTP_AUTHORIZATION=f"Bearer {org.api_token}",
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_credits"]) == Decimal("0")
        assert Decimal(data["total_usage"]) == Decimal("0")
        assert Decimal(data["balance"]) == Decimal("0")

    def test_correct_balance_after_credit_entries(self, client, org):
        """Returns correct balance after credit entries."""
        CreditLedgerEntry.objects.create(
            organization=org,
            entry_type="TOPUP",
            amount=Decimal("100.000000"),
            balance_after=Decimal("100.000000"),
        )
        CreditLedgerEntry.objects.create(
            organization=org,
            entry_type="SPEND",
            amount=Decimal("25.500000"),
            balance_after=Decimal("74.500000"),
        )
        response = client.get(
            "/api/v1/credits",
            HTTP_AUTHORIZATION=f"Bearer {org.api_token}",
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_credits"]) == Decimal("100")
        assert Decimal(data["total_usage"]) == Decimal("25.5")
        assert Decimal(data["balance"]) == Decimal("74.5")


@pytest.mark.django_db
class TestPricingPage:
    """GET /pricing/"""

    def test_pricing_returns_200(self, client):
        """Returns 200."""
        response = client.get("/pricing/")
        assert response.status_code == 200

    def test_pricing_contains_plan_names(self, client):
        """Contains plan names (Free, Pay-as-you-go, Enterprise)."""
        response = client.get("/pricing/")
        content = response.content.decode()
        assert "Free" in content
        assert "Pay-as-you-go" in content
        assert "Enterprise" in content


@pytest.mark.django_db
class TestModelsCatalogPage:
    """GET /models/"""

    def test_models_catalog_returns_200(self, client):
        """Returns 200."""
        response = client.get("/models/")
        assert response.status_code == 200

    def test_models_catalog_shows_models(self, client, provider_model):
        """Shows models when they exist."""
        response = client.get("/models/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "GPT-4o Mini" in content
