import uuid

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
