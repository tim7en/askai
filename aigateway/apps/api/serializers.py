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


class ModelPricingSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    completion = serializers.CharField()
    request = serializers.CharField()
    image = serializers.CharField()
    audio = serializers.CharField()
    internal_reasoning = serializers.CharField()
    web_search = serializers.CharField()
    input_cache_read = serializers.CharField()
    input_cache_write = serializers.CharField()


class ModelListItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    created = serializers.IntegerField()
    context_length = serializers.IntegerField()
    modality = serializers.CharField()
    pricing = ModelPricingSerializer()
    supported_parameters = serializers.ListField()
    is_free = serializers.BooleanField()
    provider = serializers.CharField()


class ChatCompletionRequestSerializer(serializers.Serializer):
    model = serializers.CharField()
    messages = serializers.ListField(child=serializers.DictField())
    stream = serializers.BooleanField(required=False, default=False)
    max_tokens = serializers.IntegerField(required=False, default=2048)
    temperature = serializers.FloatField(required=False, default=0.7)
    tools = serializers.ListField(required=False, default=list)
    tool_choice = serializers.JSONField(required=False, default=None)


class CreditsSerializer(serializers.Serializer):
    total_credits = serializers.DecimalField(max_digits=12, decimal_places=6)
    total_usage = serializers.DecimalField(max_digits=12, decimal_places=6)
    balance = serializers.DecimalField(max_digits=12, decimal_places=6)


class KeyInfoSerializer(serializers.Serializer):
    key_prefix = serializers.CharField()
    name = serializers.CharField()
    is_free_tier = serializers.BooleanField()
    credit_limit = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    rate_limit_rpm = serializers.IntegerField(allow_null=True)
    rate_limit_rpd = serializers.IntegerField(allow_null=True)
    usage = serializers.DecimalField(max_digits=12, decimal_places=6)
