import csv
import time as _time
import uuid as uuid_mod

from django.db import models
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aigateway.apps.ai_gateway.router import route_and_generate
from aigateway.apps.prompt_templates.models import PromptTemplate
from aigateway.apps.usage.models import UsageEvent

from .permissions import IsOrgMember
from .serializers import (
    AIGenerateSerializer,
    ChatCompletionRequestSerializer,
    CreditsSerializer,
    KeyInfoSerializer,
    PromptTemplateSerializer,
    UsageEventSerializer,
)


class AIGenerateView(APIView):
    """POST /api/v1/ai/generate – unified AI generation endpoint."""

    permission_classes = [IsOrgMember]

    def post(self, request):
        serializer = AIGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        org = getattr(request, "org", None)
        if not org:
            return Response({"error": "No organization context"}, status=400)

        user = request.user if request.user and request.user.is_authenticated else None

        try:
            result = route_and_generate(
                org=org,
                user=user,
                task_type=data["task_type"],
                input_text=data["input"],
                system_text=data.get("system", ""),
                preferred_provider=data.get("preferred_provider", ""),
                preferred_model=data.get("preferred_model", ""),
                max_cost_usd=data.get("max_cost_usd", 0.20),
                stream=data.get("stream", False),
            )
            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class UsageListView(generics.ListAPIView):
    """GET /api/v1/usage – list usage events for the org."""

    serializer_class = UsageEventSerializer
    permission_classes = [IsOrgMember]

    def get_queryset(self):
        org = getattr(self.request, "org", None)
        if not org:
            return UsageEvent.objects.none()
        return UsageEvent.objects.filter(organization=org)


class UsageExportCSVView(APIView):
    """GET /api/v1/usage/export.csv"""

    permission_classes = [IsOrgMember]

    def get(self, request):
        org = getattr(request, "org", None)
        if not org:
            return Response({"error": "No organization context"}, status=400)
        events = UsageEvent.objects.filter(organization=org).order_by("-created_at")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="usage.csv"'
        writer = csv.writer(response)
        writer.writerow(["Date", "Provider", "Model", "Units In", "Units Out", "Total", "Cost USD"])
        for e in events:
            writer.writerow([
                e.created_at.isoformat(), e.provider, e.model,
                e.units_in, e.units_out, e.total_units, str(e.cost_usd_estimate),
            ])
        return response


class PromptTemplateListCreateView(generics.ListCreateAPIView):
    """CRUD /api/v1/templates"""

    serializer_class = PromptTemplateSerializer
    permission_classes = [IsOrgMember]

    def get_queryset(self):
        org = getattr(self.request, "org", None)
        if not org:
            return PromptTemplate.objects.none()
        return PromptTemplate.objects.filter(organization=org)

    def perform_create(self, serializer):
        org = getattr(self.request, "org", None)
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(organization=org, created_by=user)


class PromptTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PromptTemplateSerializer
    permission_classes = [IsOrgMember]

    def get_queryset(self):
        org = getattr(self.request, "org", None)
        if not org:
            return PromptTemplate.objects.none()
        return PromptTemplate.objects.filter(organization=org)


# ---------------------------------------------------------------------------
# OpenAI-compatible gateway endpoints
# ---------------------------------------------------------------------------


def _format_model(model):
    """Format a ProviderModel instance into OpenAI-compatible model dict."""
    from decimal import Decimal

    def _price_str(per_token, per_1k_fallback):
        if per_token:
            return str(per_token)
        if per_1k_fallback:
            return str(per_1k_fallback / Decimal("1000"))
        return "0"

    created_ts = int(model.created.timestamp()) if model.created else 0
    ctx_len = model.context_length or model.context_limit or 0

    return {
        "id": f"{model.provider.slug}/{model.slug or model.provider_model_id}",
        "name": model.name,
        "description": model.description,
        "created": created_ts,
        "context_length": ctx_len,
        "modality": model.modality,
        "pricing": {
            "prompt": _price_str(model.price_prompt, model.input_price_per_1k_units),
            "completion": _price_str(model.price_completion, model.output_price_per_1k_units),
            "request": str(model.price_request),
            "image": str(model.price_image),
            "audio": str(model.price_audio),
            "internal_reasoning": str(model.price_internal_reasoning),
            "web_search": str(model.price_web_search),
            "input_cache_read": str(model.price_input_cache_read),
            "input_cache_write": str(model.price_input_cache_write),
        },
        "supported_parameters": model.supported_parameters or [],
        "is_free": model.is_free,
        "provider": model.provider.slug,
    }


class ModelsListView(APIView):
    """GET /api/v1/models – list all enabled models."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        from aigateway.apps.providers.models import ProviderModel

        models = (
            ProviderModel.objects.filter(is_enabled=True)
            .select_related("provider")
            .order_by("provider__slug", "name")
        )
        data = [_format_model(m) for m in models]
        return Response({"data": data})


class ModelDetailView(APIView):
    """GET /api/v1/models/{provider_slug}/{model_slug_or_id}"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, model_id):
        from aigateway.apps.providers.models import ProviderModel

        parts = model_id.split("/", 1)
        if len(parts) != 2:
            return Response({"error": "Invalid model ID format. Expected 'provider/model'."}, status=400)

        provider_slug, model_slug = parts
        model = (
            ProviderModel.objects.filter(
                is_enabled=True,
                provider__slug=provider_slug,
            )
            .filter(
                models.Q(slug=model_slug) | models.Q(provider_model_id=model_slug)
            )
            .select_related("provider")
            .first()
        )
        if not model:
            return Response({"error": "Model not found."}, status=404)

        return Response(_format_model(model))


class ChatCompletionsView(APIView):
    """POST /api/v1/chat/completions – OpenAI-compatible chat completions."""

    permission_classes = [IsAuthenticated | IsOrgMember]

    def post(self, request):
        serializer = ChatCompletionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        org = getattr(request, "org", None)
        if not org:
            return Response({"error": "No organization context."}, status=400)

        user = request.user if request.user and request.user.is_authenticated else None

        # Parse model ID to extract provider and model
        model_id = data["model"]
        parts = model_id.split("/", 1)
        preferred_provider = parts[0] if len(parts) == 2 else ""
        preferred_model = parts[1] if len(parts) == 2 else model_id

        # Build input from messages
        messages = data["messages"]
        system_text = ""
        input_text = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system_text = content
            elif role == "user":
                input_text = content

        try:
            result = route_and_generate(
                org=org,
                user=user,
                task_type="chat",
                input_text=input_text,
                system_text=system_text,
                preferred_provider=preferred_provider,
                preferred_model=preferred_model,
                max_cost_usd=0.20,
                stream=data.get("stream", False),
            )

            completion_id = f"chatcmpl-{uuid_mod.uuid4().hex}"

            response_data = {
                "id": completion_id,
                "object": "chat.completion",
                "created": int(_time.time()),
                "model": data["model"],
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result.get("output_text", ""),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": result.get("units_in", 0),
                    "completion_tokens": result.get("units_out", 0),
                    "total_tokens": result.get("total_units", 0),
                },
            }
            return Response(response_data)

        except ValueError as e:
            return Response({"error": {"message": str(e), "type": "invalid_request_error"}}, status=400)
        except Exception as e:
            return Response({"error": {"message": str(e), "type": "server_error"}}, status=500)


class CreditsView(APIView):
    """GET /api/v1/credits – credit balance for the organization."""

    permission_classes = [IsAuthenticated | IsOrgMember]

    def get(self, request):
        from decimal import Decimal

        from django.db.models import Sum

        from aigateway.apps.billing.models import CreditLedgerEntry

        org = getattr(request, "org", None)
        if not org:
            return Response({"error": "No organization context."}, status=400)

        entries = CreditLedgerEntry.objects.filter(organization=org)

        topups = (
            entries.filter(entry_type__in=["TOPUP", "ADJUSTMENT", "REFUND"])
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        spends = (
            entries.filter(entry_type="SPEND")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        # SPEND amounts are stored as positive values
        balance = topups - spends

        data = {
            "total_credits": topups,
            "total_usage": spends,
            "balance": balance,
        }
        serializer = CreditsSerializer(data)
        return Response(serializer.data)


class KeyInfoView(APIView):
    """GET /api/v1/key – info about the current API key."""

    permission_classes = [IsAuthenticated | IsOrgMember]

    def get(self, request):
        from decimal import Decimal

        from django.db.models import Sum

        from aigateway.apps.billing.models import CreditLedgerEntry

        api_key = getattr(request, "api_key", None)
        if not api_key:
            return Response({"error": "No API key context."}, status=400)

        org = getattr(request, "org", None)
        usage = Decimal("0")
        if org:
            usage = (
                CreditLedgerEntry.objects.filter(organization=org, entry_type="SPEND")
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
            )

        data = {
            "key_prefix": api_key.prefix,
            "name": api_key.name,
            "is_free_tier": api_key.is_free_tier,
            "credit_limit": api_key.credit_limit,
            "rate_limit_rpm": api_key.rate_limit_rpm,
            "rate_limit_rpd": api_key.rate_limit_rpd,
            "usage": usage,
        }
        serializer = KeyInfoSerializer(data)
        return Response(serializer.data)
