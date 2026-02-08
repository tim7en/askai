"""Tests for RBAC/permissions enforcement."""

import pytest
from django.test import Client

from aigateway.apps.orgs.models import Membership, Organization


@pytest.mark.django_db
class TestPermissions:
    def test_unauthenticated_user_redirected_from_dashboard(self, client):
        """Unauthenticated users cannot access /app/."""
        response = client.get("/app/")
        assert response.status_code in (301, 302)
        assert "login" in response.url or "auth" in response.url

    def test_authenticated_user_without_org_redirected_to_onboarding(self, client, user):
        """User without org membership is redirected to onboarding."""
        client.force_login(user)
        response = client.get("/app/")
        assert response.status_code in (301, 302)
        assert "onboarding" in response.url

    def test_authenticated_user_with_org_can_access_dashboard(self, client, user, membership):
        """User with org membership can access dashboard."""
        client.force_login(user)
        response = client.get("/app/")
        assert response.status_code == 200

    def test_member_cannot_invite(self, client, db):
        """A MEMBER-role user cannot invite others."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        member = User.objects.create_user(email="member@test.com", username="member", password="pass1234")
        org = Organization.objects.create(name="Org2", slug="org2")
        Membership.objects.create(user=member, organization=org, role=Membership.Role.MEMBER)

        client.force_login(member)
        response = client.get("/app/members/invite/")
        # Member should be redirected away from invite
        assert response.status_code in (301, 302)

    def test_api_requires_auth(self, client):
        """API endpoints require authentication."""
        response = client.post("/api/v1/ai/generate", data={}, content_type="application/json")
        assert response.status_code in (401, 403)

    def test_api_with_org_token(self, client, org, membership, credential, provider_model):
        """API works with org token authentication."""
        response = client.get(
            "/api/v1/usage",
            HTTP_AUTHORIZATION=f"Bearer {org.api_token}",
        )
        assert response.status_code == 200
