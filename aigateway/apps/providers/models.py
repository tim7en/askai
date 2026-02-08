import uuid

from django.conf import settings
from django.db import models

from cryptography.fernet import Fernet


def get_fernet():
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError("ENCRYPTION_KEY is not set in settings")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class Provider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "providers_provider"

    def __str__(self):
        return self.name


class ProviderModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="models")
    name = models.CharField(max_length=200)
    provider_model_id = models.CharField(max_length=200, help_text="Model ID as sent to the provider API")
    is_enabled = models.BooleanField(default=True)
    input_price_per_1k_units = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    output_price_per_1k_units = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    context_limit = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "providers_providermodel"
        unique_together = ["provider", "provider_model_id"]

    def __str__(self):
        return f"{self.provider.name} / {self.name}"


class OrgProviderCredential(models.Model):
    class Mode(models.TextChoices):
        BYO = "BYO", "Bring Your Own"
        MANAGED = "MANAGED", "Managed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "orgs.Organization", on_delete=models.CASCADE, related_name="credentials"
    )
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="credentials")
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.BYO)
    encrypted_secret = models.BinaryField(help_text="Fernet-encrypted API key")
    secret_last4 = models.CharField(max_length=4, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "providers_orgprovidercredential"
        unique_together = ["organization", "provider", "mode"]

    def __str__(self):
        return f"{self.organization.name} / {self.provider.name} ({self.mode})"

    def set_secret(self, plaintext: str):
        f = get_fernet()
        self.encrypted_secret = f.encrypt(plaintext.encode())
        self.secret_last4 = plaintext[-4:] if len(plaintext) >= 4 else plaintext

    def get_secret(self) -> str:
        f = get_fernet()
        return f.decrypt(bytes(self.encrypted_secret)).decode()
