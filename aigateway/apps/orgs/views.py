from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import OrganizationForm
from .models import Membership, OrgPolicy


@login_required
def onboarding_view(request):
    if request.user.memberships.exists():
        return redirect("web:dashboard")
    if request.method == "POST":
        form = OrganizationForm(request.POST)
        if form.is_valid():
            org = form.save()
            Membership.objects.create(user=request.user, organization=org, role=Membership.Role.OWNER)
            OrgPolicy.objects.create(organization=org)
            return redirect("web:dashboard")
    else:
        form = OrganizationForm()
    return render(request, "orgs/onboarding.html", {"form": form})
