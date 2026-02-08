"""Tests for usage logging."""

import pytest
from unittest.mock import patch

from aigateway.apps.ai_gateway.router import route_and_generate
from aigateway.apps.usage.models import UsageEvent


@pytest.mark.django_db
class TestUsageLogging:
    def test_usage_event_created_on_success(self, org, user, credential, provider_model):
        """A successful generate call creates a UsageEvent."""
        with patch("aigateway.apps.providers.adapters.OpenAIAdapter.generate") as mock_gen:
            mock_gen.return_value = {"output_text": "Hello", "units_in": 10, "units_out": 20}
            route_and_generate(
                org=org, user=user, task_type="chat",
                input_text="Hi", max_cost_usd=1.0,
            )

        events = UsageEvent.objects.filter(organization=org)
        assert events.count() == 1
        event = events.first()
        assert event.units_in == 10
        assert event.units_out == 20
        assert event.total_units == 30
        assert event.provider == "openai"

    def test_no_usage_event_on_failure(self, org, user, credential, provider_model):
        """A failed generate call does NOT create a UsageEvent."""
        with patch("aigateway.apps.providers.adapters.OpenAIAdapter.generate") as mock_gen:
            mock_gen.side_effect = Exception("fail")
            with pytest.raises(Exception):
                route_and_generate(
                    org=org, user=user, task_type="chat",
                    input_text="Hi", max_cost_usd=1.0,
                )

        assert UsageEvent.objects.filter(organization=org).count() == 0

    def test_cost_estimate_calculated(self, org, user, credential, provider_model):
        """Cost estimate is calculated from model prices."""
        with patch("aigateway.apps.providers.adapters.OpenAIAdapter.generate") as mock_gen:
            mock_gen.return_value = {"output_text": "OK", "units_in": 1000, "units_out": 500}
            route_and_generate(
                org=org, user=user, task_type="chat",
                input_text="Test", max_cost_usd=1.0,
            )

        event = UsageEvent.objects.filter(organization=org).first()
        # cost = 1000/1000 * 0.00015 + 500/1000 * 0.0006 = 0.00015 + 0.0003 = 0.00045
        assert float(event.cost_usd_estimate) == pytest.approx(0.00045, abs=1e-6)
