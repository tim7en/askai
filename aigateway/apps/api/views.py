import csv

from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aigateway.apps.ai_gateway.router import route_and_generate
from aigateway.apps.prompt_templates.models import PromptTemplate
from aigateway.apps.usage.models import UsageEvent

from .permissions import IsOrgMember
from .serializers import AIGenerateSerializer, PromptTemplateSerializer, UsageEventSerializer


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
