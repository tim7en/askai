"""Tests for AI routing and fallback logic."""

import pytest
from unittest.mock import patch, MagicMock

from aigateway.apps.ai_gateway.router import route_and_generate
from aigateway.apps.providers.models import Provider, ProviderModel, OrgProviderCredential


@pytest.mark.django_db
class TestRouterFallback:
    def test_no_credentials_raises(self, org, user):
        """Router raises ValueError when no credentials configured."""
        with pytest.raises(ValueError, match="No active provider credentials"):
            route_and_generate(
                org=org, user=user, task_type="chat",
                input_text="Hello", max_cost_usd=1.0,
            )

    def test_preferred_provider_used(self, org, user, credential, provider_model):
        """Router uses preferred provider when specified."""
        with patch("aigateway.apps.providers.adapters.OpenAIAdapter.generate") as mock_gen:
            mock_gen.return_value = {"output_text": "Hi", "units_in": 5, "units_out": 10}
            result = route_and_generate(
                org=org, user=user, task_type="chat",
                input_text="Hello", preferred_provider="openai",
                max_cost_usd=1.0,
            )
            assert result["provider"] == "openai"
            assert result["output_text"] == "Hi"

    def test_cheapest_model_selected(self, org, user, credential, provider):
        """Router picks cheapest model within cost ceiling."""
        # Create expensive model
        ProviderModel.objects.create(
            provider=provider, name="GPT-4", provider_model_id="gpt-4",
            input_price_per_1k_units=30, output_price_per_1k_units=60,
        )
        # Create cheap model
        cheap = ProviderModel.objects.create(
            provider=provider, name="GPT-4o-mini", provider_model_id="gpt-4o-mini",
            input_price_per_1k_units=0.00015, output_price_per_1k_units=0.0006,
        )

        with patch("aigateway.apps.providers.adapters.OpenAIAdapter.generate") as mock_gen:
            mock_gen.return_value = {"output_text": "Response", "units_in": 10, "units_out": 20}
            result = route_and_generate(
                org=org, user=user, task_type="chat",
                input_text="Test", max_cost_usd=0.10,
            )
            # Should pick cheaper model
            assert result["model"] == "gpt-4o-mini"

    def test_error_logged_on_failure(self, org, user, credential, provider_model):
        """Router logs errors when adapter fails."""
        from aigateway.apps.ai_gateway.models import AIRequest

        with patch("aigateway.apps.providers.adapters.OpenAIAdapter.generate") as mock_gen:
            mock_gen.side_effect = Exception("API Error")
            with pytest.raises(Exception, match="API Error"):
                route_and_generate(
                    org=org, user=user, task_type="chat",
                    input_text="Test", max_cost_usd=1.0,
                )

        # Check error was logged
        req = AIRequest.objects.filter(organization=org).first()
        assert req is not None
        assert req.status == "ERROR"
        assert "API Error" in req.error_message
