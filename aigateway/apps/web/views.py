import csv
import time

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from aigateway.apps.ai_gateway.models import AIRequest
from aigateway.apps.ai_gateway.router import route_and_generate
from aigateway.apps.billing.models import Invoice, Subscription
from aigateway.apps.orgs.models import Membership, OrgPolicy
from aigateway.apps.prompt_templates.models import PromptTemplate
from aigateway.apps.providers.models import OrgProviderCredential, Provider, ProviderModel
from aigateway.apps.usage.models import UsageEvent

from .decorators import org_required


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("web:dashboard")
    return render(request, "web/landing.html")


@org_required
def dashboard_view(request):
    org = request.org
    recent_requests = AIRequest.objects.filter(organization=org)[:10]
    total_usage = UsageEvent.objects.filter(organization=org).aggregate(
        total_cost=Sum("cost_usd_estimate"),
        total_units=Sum("total_units"),
    )
    return render(request, "web/dashboard.html", {
        "org": org,
        "membership": request.membership,
        "recent_requests": recent_requests,
        "total_cost": total_usage["total_cost"] or 0,
        "total_units": total_usage["total_units"] or 0,
    })


@org_required
def playground_view(request):
    org = request.org
    result = None
    error = None

    if request.method == "POST":
        task_type = request.POST.get("task_type", "chat")
        input_text = request.POST.get("input", "")
        system_text = request.POST.get("system", "")
        preferred_provider = request.POST.get("preferred_provider", "")
        preferred_model = request.POST.get("preferred_model", "")
        max_cost = request.POST.get("max_cost_usd", "0.20")

        start = time.time()
        try:
            result = route_and_generate(
                org=org,
                user=request.user,
                task_type=task_type,
                input_text=input_text,
                system_text=system_text,
                preferred_provider=preferred_provider,
                preferred_model=preferred_model,
                max_cost_usd=float(max_cost),
                stream=False,
            )
        except Exception as e:
            error = str(e)
        elapsed = int((time.time() - start) * 1000)
        if result:
            result["latency_ms"] = elapsed

    providers = Provider.objects.filter(is_enabled=True)
    models = ProviderModel.objects.filter(is_enabled=True).select_related("provider")
    templates = PromptTemplate.objects.filter(organization=org)[:20]

    return render(request, "web/playground.html", {
        "org": org,
        "result": result,
        "error": error,
        "providers": providers,
        "models": models,
        "templates": templates,
    })


@org_required
def templates_view(request):
    templates = PromptTemplate.objects.filter(organization=request.org)
    return render(request, "web/templates.html", {"org": request.org, "templates": templates})


@org_required
def template_create_view(request):
    if request.method == "POST":
        PromptTemplate.objects.create(
            organization=request.org,
            name=request.POST.get("name", ""),
            task_type=request.POST.get("task_type", "chat"),
            system_text=request.POST.get("system_text", ""),
            user_text=request.POST.get("user_text", ""),
            created_by=request.user,
        )
        return redirect("web:templates")
    return render(request, "web/template_create.html", {"org": request.org})


@org_required
def usage_view(request):
    events = UsageEvent.objects.filter(organization=request.org).select_related("ai_request")[:100]
    return render(request, "web/usage.html", {"org": request.org, "events": events})


@org_required
def usage_export_csv(request):
    events = UsageEvent.objects.filter(organization=request.org).order_by("-created_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="usage.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Provider", "Model", "Units In", "Units Out", "Total", "Cost USD"])
    for e in events:
        writer.writerow([
            e.created_at.isoformat(),
            e.provider,
            e.model,
            e.units_in,
            e.units_out,
            e.total_units,
            str(e.cost_usd_estimate),
        ])
    return response


@org_required
def providers_view(request):
    providers = Provider.objects.filter(is_enabled=True).prefetch_related("models")
    credentials = OrgProviderCredential.objects.filter(organization=request.org)
    return render(request, "web/providers.html", {
        "org": request.org,
        "providers": providers,
        "credentials": credentials,
    })


@org_required
def provider_add_credential_view(request):
    if request.method == "POST":
        provider_id = request.POST.get("provider")
        mode = request.POST.get("mode", "BYO")
        api_key = request.POST.get("api_key", "")
        provider = Provider.objects.get(id=provider_id)
        cred, created = OrgProviderCredential.objects.get_or_create(
            organization=request.org,
            provider=provider,
            mode=mode,
            defaults={"encrypted_secret": b"", "is_active": True},
        )
        cred.set_secret(api_key)
        cred.is_active = True
        cred.save()
        return redirect("web:providers")
    providers = Provider.objects.filter(is_enabled=True)
    return render(request, "web/provider_add.html", {"org": request.org, "providers": providers})


@org_required
def members_view(request):
    members = Membership.objects.filter(organization=request.org).select_related("user")
    return render(request, "web/members.html", {"org": request.org, "members": members, "membership": request.membership})


@org_required
def member_invite_view(request):
    if request.membership.role not in (Membership.Role.OWNER, Membership.Role.ADMIN):
        return redirect("web:members")
    if request.method == "POST":
        from django.contrib.auth import get_user_model

        User = get_user_model()
        email = request.POST.get("email", "")
        role = request.POST.get("role", Membership.Role.MEMBER)
        try:
            user = User.objects.get(email=email)
            Membership.objects.get_or_create(
                user=user, organization=request.org, defaults={"role": role}
            )
        except User.DoesNotExist:
            pass  # In production: send invite email
        return redirect("web:members")
    return render(request, "web/member_invite.html", {"org": request.org})


@org_required
def billing_view(request):
    invoices = Invoice.objects.filter(organization=request.org)
    subscriptions = Subscription.objects.filter(organization=request.org)
    return render(request, "web/billing.html", {
        "org": request.org,
        "invoices": invoices,
        "subscriptions": subscriptions,
    })


@org_required
def settings_view(request):
    try:
        policy = request.org.policy
    except OrgPolicy.DoesNotExist:
        policy = OrgPolicy.objects.create(organization=request.org)

    if request.method == "POST":
        policy.mode_default = request.POST.get("mode_default", "BYO")
        policy.monthly_cap_usd = request.POST.get("monthly_cap_usd", 100)
        policy.hard_cap = request.POST.get("hard_cap") == "on"
        policy.retention_days = request.POST.get("retention_days", 90)
        policy.save()
        return redirect("web:settings")

    return render(request, "web/settings.html", {"org": request.org, "policy": policy})


def terms_view(request):
    return render(request, "legal/terms.html")


def privacy_view(request):
    return render(request, "legal/privacy.html")
