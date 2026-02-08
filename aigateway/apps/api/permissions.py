from rest_framework.permissions import BasePermission

from aigateway.apps.orgs.models import Membership


class IsOrgMember(BasePermission):
    """User must be a member of the org."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            # Check if org token auth was used
            return hasattr(request, "org") and request.org is not None
        org = getattr(request, "org", None)
        if not org:
            return False
        return Membership.objects.filter(user=request.user, organization=org).exists()


class IsOrgAdmin(BasePermission):
    """User must be OWNER or ADMIN of the org."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org = getattr(request, "org", None)
        if not org:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization=org,
            role__in=[Membership.Role.OWNER, Membership.Role.ADMIN],
        ).exists()
