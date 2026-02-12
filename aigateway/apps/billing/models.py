import hashlib
import secrets
import uuid

from django.conf import settings
from django.db import models


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    monthly_fee_usd = models.DecimalField(max_digits=10, decimal_places=2)
    included_units = models.IntegerField(default=0)
    overage_price_per_1k_units = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        db_table = "billing_plan"

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CANCELLED = "CANCELLED", "Cancelled"
        PAST_DUE = "PAST_DUE", "Past Due"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    period_start = models.DateField()
    period_end = models.DateField()

    class Meta:
        db_table = "billing_subscription"

    def __str__(self):
        return f"{self.organization.name} – {self.plan.name}"


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"
        PAID = "PAID", "Paid"
        VOID = "VOID", "Void"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, related_name="invoices")
    period_start = models.DateField()
    period_end = models.DateField()
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_invoice"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.id} – ${self.amount_usd}"


class PaymentTransaction(models.Model):
    class ProviderName(models.TextChoices):
        CLICK = "CLICK", "Click"
        PAYME = "PAYME", "Payme"
        BANK = "BANK", "Bank Transfer"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    provider_name = models.CharField(max_length=20, choices=ProviderName.choices, default=ProviderName.BANK)
    reference = models.CharField(max_length=200, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_paymenttransaction"

    def __str__(self):
        return f"Payment {self.id} – {self.status}"


class CreditLedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        TOPUP = "TOPUP", "Top-up"
        SPEND = "SPEND", "Spend"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        REFUND = "REFUND", "Refund"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "orgs.Organization", on_delete=models.CASCADE, related_name="credit_ledger_entries"
    )
    entry_type = models.CharField(max_length=20, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    balance_after = models.DecimalField(max_digits=12, decimal_places=6)
    description = models.CharField(max_length=500, blank=True, default="")
    reference_id = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_creditledgerentry"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.entry_type} {self.amount} (org={self.organization_id})"


class ApiKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "orgs.Organization", on_delete=models.CASCADE, related_name="api_keys"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="api_keys"
    )
    name = models.CharField(max_length=200, default="Default")
    prefix = models.CharField(max_length=8)
    hashed_key = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rate_limit_rpm = models.IntegerField(null=True, blank=True)
    rate_limit_rpd = models.IntegerField(null=True, blank=True)
    is_free_tier = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "billing_apikey"

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @classmethod
    def create_key(cls, organization, user=None, name="Default"):
        plaintext_key = "sk-or-v1-" + secrets.token_hex(32)
        prefix = plaintext_key[:8]
        hashed_key = hashlib.sha256(plaintext_key.encode()).hexdigest()
        instance = cls.objects.create(
            organization=organization,
            user=user,
            name=name,
            prefix=prefix,
            hashed_key=hashed_key,
        )
        return instance, plaintext_key

    @classmethod
    def lookup(cls, plaintext_key):
        hashed_key = hashlib.sha256(plaintext_key.encode()).hexdigest()
        try:
            return cls.objects.get(hashed_key=hashed_key)
        except cls.DoesNotExist:
            return None


class ManagementKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "orgs.Organization", on_delete=models.CASCADE, related_name="management_keys"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="management_keys"
    )
    name = models.CharField(max_length=200, default="Default")
    prefix = models.CharField(max_length=8)
    hashed_key = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rate_limit_rpm = models.IntegerField(null=True, blank=True)
    rate_limit_rpd = models.IntegerField(null=True, blank=True)
    is_free_tier = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "billing_managementkey"

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @classmethod
    def create_key(cls, organization, user=None, name="Default"):
        plaintext_key = "sk-or-mgmt-" + secrets.token_hex(32)
        prefix = plaintext_key[:8]
        hashed_key = hashlib.sha256(plaintext_key.encode()).hexdigest()
        instance = cls.objects.create(
            organization=organization,
            user=user,
            name=name,
            prefix=prefix,
            hashed_key=hashed_key,
        )
        return instance, plaintext_key

    @classmethod
    def lookup(cls, plaintext_key):
        hashed_key = hashlib.sha256(plaintext_key.encode()).hexdigest()
        try:
            return cls.objects.get(hashed_key=hashed_key)
        except cls.DoesNotExist:
            return None
