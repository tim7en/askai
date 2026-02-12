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
            {"name": "OpenAI", "slug": "openai", "description": "AI research lab", "website_url": "https://openai.com", "data_retention_policy": "none"},
            {"name": "Anthropic", "slug": "anthropic", "description": "AI safety company", "website_url": "https://anthropic.com", "data_retention_policy": "none"},
            {"name": "Google AI", "slug": "google", "description": "Google AI services", "website_url": "https://ai.google.dev", "data_retention_policy": "30_days"},
            {"name": "Open Source", "slug": "oss", "description": "Open-source model hosting", "website_url": "", "data_retention_policy": "none"},
        ]
        for pd in providers_data:
            Provider.objects.update_or_create(
                slug=pd["slug"],
                defaults={
                    "name": pd["name"],
                    "description": pd.get("description", ""),
                    "website_url": pd.get("website_url", ""),
                    "data_retention_policy": pd.get("data_retention_policy", ""),
                },
            )

        # Models with full catalog fields
        models_data = [
            {
                "provider_slug": "openai", "name": "GPT-4o", "model_id": "gpt-4o",
                "slug": "gpt-4o", "description": "Most capable GPT-4 model with vision support.",
                "in_price": 0.005, "out_price": 0.015, "ctx": 128000,
                "context_length": 128000, "modality": "multimodal",
                "price_prompt": "0.000005", "price_completion": "0.000015",
                "supported_parameters": ["tools", "structured_output", "vision"],
            },
            {
                "provider_slug": "openai", "name": "GPT-4o Mini", "model_id": "gpt-4o-mini",
                "slug": "gpt-4o-mini", "description": "Fast, affordable small model for lightweight tasks.",
                "in_price": 0.00015, "out_price": 0.0006, "ctx": 128000,
                "context_length": 128000, "modality": "text",
                "price_prompt": "0.00000015", "price_completion": "0.0000006",
                "supported_parameters": ["tools", "structured_output"],
            },
            {
                "provider_slug": "openai", "name": "GPT-4o Mini (Free)", "model_id": "gpt-4o-mini:free",
                "slug": "gpt-4o-mini-free", "description": "Free variant of GPT-4o Mini with rate limits.",
                "in_price": 0, "out_price": 0, "ctx": 128000,
                "context_length": 128000, "modality": "text", "is_free": True,
                "price_prompt": "0", "price_completion": "0",
                "supported_parameters": ["tools"],
            },
            {
                "provider_slug": "anthropic", "name": "Claude Sonnet 4", "model_id": "claude-sonnet-4-20250514",
                "slug": "claude-sonnet-4", "description": "Balanced performance and cost for complex tasks.",
                "in_price": 0.003, "out_price": 0.015, "ctx": 200000,
                "context_length": 200000, "modality": "text",
                "price_prompt": "0.000003", "price_completion": "0.000015",
                "price_input_cache_read": "0.0000003", "price_input_cache_write": "0.00000375",
                "supported_parameters": ["tools", "structured_output"],
            },
            {
                "provider_slug": "anthropic", "name": "Claude 3.5 Haiku", "model_id": "claude-3-5-haiku-20241022",
                "slug": "claude-3-5-haiku", "description": "Fastest Claude model for quick responses.",
                "in_price": 0.001, "out_price": 0.005, "ctx": 200000,
                "context_length": 200000, "modality": "text",
                "price_prompt": "0.000001", "price_completion": "0.000005",
                "price_input_cache_read": "0.0000001", "price_input_cache_write": "0.00000125",
                "supported_parameters": ["tools"],
            },
            {
                "provider_slug": "google", "name": "Gemini 2.0 Flash", "model_id": "gemini-2.0-flash",
                "slug": "gemini-2-0-flash", "description": "Fast multimodal model with 1M context window.",
                "in_price": 0.001, "out_price": 0.004, "ctx": 1000000,
                "context_length": 1000000, "modality": "multimodal",
                "price_prompt": "0.000001", "price_completion": "0.000004",
                "supported_parameters": ["tools", "vision"],
            },
            {
                "provider_slug": "google", "name": "Gemini 2.0 Flash (Free)", "model_id": "gemini-2.0-flash:free",
                "slug": "gemini-2-0-flash-free", "description": "Free variant of Gemini 2.0 Flash with rate limits.",
                "in_price": 0, "out_price": 0, "ctx": 1000000,
                "context_length": 1000000, "modality": "multimodal", "is_free": True,
                "price_prompt": "0", "price_completion": "0",
                "supported_parameters": ["tools", "vision"],
            },
        ]

        from decimal import Decimal

        for md in models_data:
            provider = Provider.objects.get(slug=md["provider_slug"])
            ProviderModel.objects.update_or_create(
                provider=provider,
                provider_model_id=md["model_id"],
                defaults={
                    "name": md["name"],
                    "slug": md.get("slug", ""),
                    "description": md.get("description", ""),
                    "input_price_per_1k_units": md["in_price"],
                    "output_price_per_1k_units": md["out_price"],
                    "context_limit": md["ctx"],
                    "context_length": md.get("context_length", md["ctx"]),
                    "modality": md.get("modality", "text"),
                    "is_free": md.get("is_free", False),
                    "price_prompt": Decimal(md.get("price_prompt", "0")),
                    "price_completion": Decimal(md.get("price_completion", "0")),
                    "price_input_cache_read": Decimal(md.get("price_input_cache_read", "0")),
                    "price_input_cache_write": Decimal(md.get("price_input_cache_write", "0")),
                    "supported_parameters": md.get("supported_parameters", []),
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
