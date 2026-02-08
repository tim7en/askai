import pytest
from cryptography.fernet import Fernet
from django.test import override_settings

TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _encryption_key(settings):
    settings.ENCRYPTION_KEY = TEST_ENCRYPTION_KEY


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    u = User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123",
        is_email_verified=True,
    )
    return u


@pytest.fixture
def org(db):
    from aigateway.apps.orgs.models import Organization

    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.fixture
def membership(user, org):
    from aigateway.apps.orgs.models import Membership

    return Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)


@pytest.fixture
def org_policy(org):
    from aigateway.apps.orgs.models import OrgPolicy

    return OrgPolicy.objects.create(organization=org)


@pytest.fixture
def provider(db):
    from aigateway.apps.providers.models import Provider

    return Provider.objects.create(name="OpenAI", slug="openai")


@pytest.fixture
def provider_model(provider):
    from aigateway.apps.providers.models import ProviderModel

    return ProviderModel.objects.create(
        provider=provider,
        name="GPT-4o Mini",
        provider_model_id="gpt-4o-mini",
        input_price_per_1k_units=0.00015,
        output_price_per_1k_units=0.0006,
    )


@pytest.fixture
def credential(org, provider):
    from aigateway.apps.providers.models import OrgProviderCredential

    cred = OrgProviderCredential(
        organization=org,
        provider=provider,
        mode="BYO",
        encrypted_secret=b"",
    )
    cred.set_secret("sk-test-key-12345678")
    cred.save()
    return cred
