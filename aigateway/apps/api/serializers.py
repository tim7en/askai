from rest_framework import serializers

from aigateway.apps.prompt_templates.models import PromptTemplate
from aigateway.apps.usage.models import UsageEvent


class AIGenerateSerializer(serializers.Serializer):
    task_type = serializers.ChoiceField(choices=["chat", "summarize", "translate", "code", "extract"], default="chat")
    input = serializers.CharField()
    system = serializers.CharField(required=False, default="", allow_blank=True)
    preferred_provider = serializers.CharField(required=False, default="", allow_blank=True)
    preferred_model = serializers.CharField(required=False, default="", allow_blank=True)
    max_cost_usd = serializers.FloatField(required=False, default=0.20)
    stream = serializers.BooleanField(required=False, default=False)


class UsageEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageEvent
        fields = [
            "id", "provider", "model", "units_in", "units_out",
            "total_units", "cost_usd_estimate", "created_at",
        ]


class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = [
            "id", "name", "task_type", "system_text", "user_text",
            "variables_json", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
