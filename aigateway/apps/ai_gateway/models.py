import uuid

from django.conf import settings
from django.db import models


class AIRequest(models.Model):
    class Status(models.TextChoices):
        OK = "OK", "OK"
        ERROR = "ERROR", "Error"
        BLOCKED = "BLOCKED", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, related_name="ai_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    provider = models.CharField(max_length=100)
    model = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OK)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=100, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    meta_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_gateway_airequest"
        ordering = ["-created_at"]

    def __str__(self):
        return f"AIRequest {self.id} ({self.status})"
