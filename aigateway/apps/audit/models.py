import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "orgs.Organization", on_delete=models.CASCADE, related_name="audit_logs", null=True, blank=True
    )
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100, blank=True, default="")
    target_id = models.CharField(max_length=200, blank=True, default="")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    meta_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "audit_auditlog"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.actor_user} at {self.created_at}"


def log_action(request, org, action, target_type="", target_id="", meta=None):
    """Helper to create audit log entries."""
    AuditLog.objects.create(
        organization=org,
        actor_user=request.user if request and request.user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        ip=request.META.get("REMOTE_ADDR", "") if request else "",
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500] if request else "",
        meta_json=meta or {},
    )
