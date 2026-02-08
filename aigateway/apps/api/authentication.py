from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from aigateway.apps.orgs.models import Organization


class OrgTokenAuthentication(BaseAuthentication):
    """Authenticate requests using org API token in Authorization header."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith(f"{self.keyword} "):
            return None

        token = auth[len(self.keyword) + 1 :]
        try:
            org = Organization.objects.get(api_token=token)
        except Organization.DoesNotExist:
            raise AuthenticationFailed("Invalid API token.")

        # Attach org to request for downstream use
        request.org = org
        # Return None user for token auth (org-level auth)
        return (None, org)
