from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from aigateway.apps.orgs.models import Membership, OrgPolicy, Organization
from aigateway.apps.prompt_templates.models import PromptTemplate
from aigateway.apps.providers.models import Provider, ProviderModel

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo data"

    def handle(self, *args, **options):
        # Create demo user
        user, created = User.objects.get_or_create(
            email="demo@aigateway.uz",
            defaults={
                "username": "demo",
                "is_email_verified": True,
            },
        )
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user: demo@aigateway.uz / demo1234"))

        # Create demo org
        org, created = Organization.objects.get_or_create(
            slug="demo-org",
            defaults={"name": "Demo Organization"},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created demo org: {org.name} (token: {org.api_token})"))

        # Membership
        Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={"role": Membership.Role.OWNER},
        )

        # Policy
        OrgPolicy.objects.get_or_create(
            organization=org,
            defaults={"mode_default": "BYO", "monthly_cap_usd": 100},
        )

        # Providers
        providers_data = [
            {"name": "OpenAI", "slug": "openai"},
            {"name": "Anthropic", "slug": "anthropic"},
            {"name": "Google AI", "slug": "google"},
            {"name": "Open Source", "slug": "oss"},
        ]
        for pd in providers_data:
            Provider.objects.get_or_create(slug=pd["slug"], defaults={"name": pd["name"]})

        # Models
        models_data = [
            {"provider_slug": "openai", "name": "GPT-4o", "model_id": "gpt-4o", "in_price": 0.005, "out_price": 0.015, "ctx": 128000},
            {"provider_slug": "openai", "name": "GPT-4o Mini", "model_id": "gpt-4o-mini", "in_price": 0.00015, "out_price": 0.0006, "ctx": 128000},
            {"provider_slug": "anthropic", "name": "Claude 3.5 Sonnet", "model_id": "claude-3-5-sonnet-20241022", "in_price": 0.003, "out_price": 0.015, "ctx": 200000},
            {"provider_slug": "anthropic", "name": "Claude 3.5 Haiku", "model_id": "claude-3-5-haiku-20241022", "in_price": 0.001, "out_price": 0.005, "ctx": 200000},
            {"provider_slug": "google", "name": "Gemini 1.5 Pro", "model_id": "gemini-1.5-pro", "in_price": 0.00125, "out_price": 0.005, "ctx": 2000000},
        ]

        for md in models_data:
            provider = Provider.objects.get(slug=md["provider_slug"])
            ProviderModel.objects.get_or_create(
                provider=provider,
                provider_model_id=md["model_id"],
                defaults={
                    "name": md["name"],
                    "input_price_per_1k_units": md["in_price"],
                    "output_price_per_1k_units": md["out_price"],
                    "context_limit": md["ctx"],
                },
            )

        # Prompt templates
        templates = [
            {"name": "General Chat", "task_type": "chat", "system": "You are a helpful assistant.", "user": ""},
            {"name": "Code Review", "task_type": "code", "system": "You are a senior software engineer. Review the following code.", "user": ""},
            {"name": "Summarizer", "task_type": "summarize", "system": "Summarize the following text concisely.", "user": ""},
            {"name": "Translator EN→UZ", "task_type": "translate", "system": "Translate the following English text to Uzbek.", "user": ""},
        ]
        for t in templates:
            PromptTemplate.objects.get_or_create(
                organization=org,
                name=t["name"],
                defaults={
                    "task_type": t["task_type"],
                    "system_text": t["system"],
                    "user_text": t["user"],
                    "created_by": user,
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
