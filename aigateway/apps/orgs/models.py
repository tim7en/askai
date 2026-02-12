import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    api_token = models.CharField(max_length=64, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orgs_organization"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.api_token:
            self.api_token = secrets.token_hex(32)
        super().save(*args, **kwargs)


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orgs_membership"
        unique_together = ["user", "organization"]

    def __str__(self):
        return f"{self.user.email} → {self.organization.name} ({self.role})"


class OrgPolicy(models.Model):
    class ModeDefault(models.TextChoices):
        BYO = "BYO", "Bring Your Own Keys"
        MANAGED = "MANAGED", "Managed Access"

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="policy")
    mode_default = models.CharField(max_length=10, choices=ModeDefault.choices, default=ModeDefault.BYO)
    monthly_cap_usd = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    hard_cap = models.BooleanField(default=False, help_text="Block requests when cap is reached")
    degrade_on_cap = models.BooleanField(default=True, help_text="Fall back to cheaper models on cap")
    retention_enabled = models.BooleanField(default=True)
    retention_days = models.IntegerField(default=90)
    allow_providers_json = models.JSONField(default=list, blank=True)
    allow_models_json = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "orgs_orgpolicy"

    def __str__(self):
        return f"Policy for {self.organization.name}"


class RoutingPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="routing_policies")
    name = models.CharField(max_length=200, default="Default")
    provider_allow = models.JSONField(default=list, blank=True, help_text="Allowed provider slugs")
    provider_deny = models.JSONField(default=list, blank=True, help_text="Denied provider slugs")
    region_preference = models.CharField(max_length=100, blank=True, default="")
    weights = models.JSONField(default=dict, blank=True, help_text="Provider slug -> weight mapping")
    require_no_retention = models.BooleanField(default=False, help_text="Only route to providers with no data retention")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orgs_routingpolicy"

    def __str__(self):
        return f"RoutingPolicy: {self.name} (org={self.organization.name})"
