"""
Unified AI router: chooses provider+model and calls the appropriate adapter.
"""

import logging
import time
from decimal import Decimal

from django.utils import timezone

from aigateway.apps.ai_gateway.models import AIRequest
from aigateway.apps.providers.adapters import get_adapter
from aigateway.apps.providers.models import OrgProviderCredential, ProviderModel
from aigateway.apps.usage.models import UsageEvent

logger = logging.getLogger(__name__)


def route_and_generate(
    org,
    user,
    task_type: str,
    input_text: str,
    system_text: str = "",
    preferred_provider: str = "",
    preferred_model: str = "",
    max_cost_usd: float = 0.20,
    stream: bool = False,
):
    """
    Router logic:
    1. Get org's active credentials
    2. Filter to preferred provider/model if specified
    3. Pick best available model within cost ceiling
    4. Call adapter
    5. Log AIRequest + UsageEvent
    6. Return result dict
    """
    credentials = OrgProviderCredential.objects.filter(
        organization=org, is_active=True
    ).select_related("provider")

    if not credentials.exists():
        raise ValueError("No active provider credentials configured. Add one in Providers.")

    # Filter by preferred provider
    if preferred_provider:
        filtered = credentials.filter(provider__slug=preferred_provider)
        if filtered.exists():
            credentials = filtered

    # Get available models
    available_models = ProviderModel.objects.filter(
        is_enabled=True,
        provider__in=[c.provider for c in credentials],
    ).select_related("provider").order_by("input_price_per_1k_units")

    if preferred_model:
        preferred = available_models.filter(provider_model_id=preferred_model)
        if preferred.exists():
            available_models = preferred

    if not available_models.exists():
        raise ValueError("No enabled models available for your configured providers.")

    # Pick model (cheapest within cost ceiling, or first available)
    selected_model = available_models.first()
    for m in available_models:
        # Rough estimate: 1k tokens input + 1k tokens output
        est = float(m.input_price_per_1k_units + m.output_price_per_1k_units)
        if est <= max_cost_usd:
            selected_model = m
            break

    # Get credential for the selected model's provider
    cred = credentials.filter(provider=selected_model.provider).first()
    if not cred:
        raise ValueError(f"No credential found for provider {selected_model.provider.name}")

    # Create AI request record
    ai_request = AIRequest.objects.create(
        organization=org,
        user=user,
        provider=selected_model.provider.slug,
        model=selected_model.provider_model_id,
        status=AIRequest.Status.OK,
    )

    start_time = time.time()
    try:
        adapter = get_adapter(selected_model.provider.slug)
        api_key = cred.get_secret()

        result = adapter.generate(
            api_key=api_key,
            model=selected_model.provider_model_id,
            prompt=input_text,
            system=system_text,
            max_tokens=2048,
            temperature=0.7,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        ai_request.finished_at = timezone.now()
        ai_request.latency_ms = elapsed_ms
        ai_request.save()

        # Calculate cost estimate
        units_in = result.get("units_in", 0)
        units_out = result.get("units_out", 0)
        total_units = units_in + units_out
        cost_estimate = (
            Decimal(units_in) / 1000 * selected_model.input_price_per_1k_units
            + Decimal(units_out) / 1000 * selected_model.output_price_per_1k_units
        )

        # Log usage
        UsageEvent.objects.create(
            ai_request=ai_request,
            organization=org,
            user=user,
            provider=selected_model.provider.slug,
            model=selected_model.provider_model_id,
            units_in=units_in,
            units_out=units_out,
            total_units=total_units,
            cost_usd_estimate=cost_estimate,
        )

        return {
            "output_text": result.get("output_text", ""),
            "provider": selected_model.provider.slug,
            "model": selected_model.provider_model_id,
            "units_in": units_in,
            "units_out": units_out,
            "total_units": total_units,
            "cost_usd_estimate": str(cost_estimate),
            "request_id": str(ai_request.id),
            "latency_ms": elapsed_ms,
        }

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        ai_request.status = AIRequest.Status.ERROR
        ai_request.error_message = str(e)[:500]
        ai_request.latency_ms = elapsed_ms
        ai_request.finished_at = timezone.now()
        ai_request.save()
        raise
