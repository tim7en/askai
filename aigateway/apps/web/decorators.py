from functools import wraps

from django.shortcuts import redirect

from aigateway.apps.orgs.models import Membership


def org_required(view_func):
    """Decorator: ensures user has an org membership, redirects to onboarding if not."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        membership = Membership.objects.filter(user=request.user).select_related("organization").first()
        if not membership:
            return redirect("orgs:onboarding")
        request.org = membership.organization
        request.membership = membership
        return view_func(request, *args, **kwargs)

    return wrapper
