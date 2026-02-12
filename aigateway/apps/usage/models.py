import uuid

from django.conf import settings
from django.db import models


class UsageEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ai_request = models.ForeignKey(
        "ai_gateway.AIRequest", on_delete=models.CASCADE, related_name="usage_events"
    )
    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, related_name="usage_events")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    provider = models.CharField(max_length=100)
    model = models.CharField(max_length=200)
    units_in = models.IntegerField(default=0)
    units_out = models.IntegerField(default=0)
    total_units = models.IntegerField(default=0)
    cost_usd_estimate = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    meta_json = models.JSONField(default=dict, blank=True)
    api_key_id = models.UUIDField(null=True, blank=True)
    provider_id = models.UUIDField(null=True, blank=True)
    endpoint_id = models.UUIDField(null=True, blank=True)
    reasoning_tokens = models.IntegerField(default=0)
    cached_tokens = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default="success", help_text="success or fail")
    fallback_chain = models.JSONField(default=list, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")

    class Meta:
        db_table = "usage_usageevent"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Usage {self.id}: {self.total_units} units"
