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


class ApiKeyAuthentication(BaseAuthentication):
    """Authenticate requests using Bearer sk-or-v1-... API keys."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith(f"{self.keyword} "):
            return None

        token = auth[len(self.keyword) + 1 :]
        if not token.startswith("sk-or-v1-"):
            return None

        from aigateway.apps.billing.models import ApiKey

        api_key = ApiKey.lookup(token)
        if api_key is None:
            raise AuthenticationFailed("Invalid API key.")
        if not api_key.is_active:
            raise AuthenticationFailed("API key is inactive.")

        request.org = api_key.organization
        request.api_key = api_key
        user = api_key.user if api_key.user else None
        return (user, api_key) if user else (None, api_key)


class ManagementKeyAuthentication(BaseAuthentication):
    """Authenticate requests using Bearer sk-or-mgmt-... management keys."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith(f"{self.keyword} "):
            return None

        token = auth[len(self.keyword) + 1 :]
        if not token.startswith("sk-or-mgmt-"):
            return None

        from aigateway.apps.billing.models import ManagementKey

        mgmt_key = ManagementKey.lookup(token)
        if mgmt_key is None:
            raise AuthenticationFailed("Invalid management key.")
        if not mgmt_key.is_active:
            raise AuthenticationFailed("Management key is inactive.")

        request.org = mgmt_key.organization
        request.api_key = mgmt_key
        user = mgmt_key.user if mgmt_key.user else None
        return (user, mgmt_key) if user else (None, mgmt_key)
