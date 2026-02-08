# AIGateway UZ

A production-ready Django web app that provides a unified interface for organizations in Uzbekistan to access multiple AI providers (OpenAI, Anthropic, Google, etc.) through a single gateway.

## Features

- **Unified AI Gateway** – One API endpoint to access OpenAI, Anthropic, Google AI, and more
- **BYO Keys Mode** – Organizations bring their own API keys; pay providers directly
- **Managed Access Mode** – Platform provides API access; organizations pay locally
- **Playground** – Interactive prompt runner with cost and token tracking
- **Usage Analytics** – Track every request, export CSV, set spending caps
- **Team Management** – RBAC with Owner/Admin/Member roles
- **Credential Encryption** – Fernet-encrypted API keys at rest
- **Billing** – Invoices, plans, manual bank transfer workflow
- **Prompt Templates** – Save and reuse prompt configurations
- **Clean UI** – Bootstrap 5 with a minimalist, professional design

## Tech Stack

- **Backend**: Python 3.12+, Django 5.x, Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Frontend**: Django templates + Bootstrap 5 (server-rendered)
- **Security**: Fernet encryption, RBAC, CSRF, rate limiting
- **Deployment**: Docker + docker-compose, Gunicorn + WhiteNoise
- **Testing**: pytest + pytest-django
- **Linting**: ruff

## Quick Start

### Prerequisites

- Python 3.12+
- pip

### Setup

```bash
# Clone the repo
git clone <repository-url>
cd askai

# Install dependencies
pip install django django-environ djangorestframework psycopg2-binary gunicorn whitenoise cryptography httpx django-ratelimit

# Copy env file and configure
cp .env.example .env
# Edit .env – generate ENCRYPTION_KEY with:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed demo data (demo user: demo@aigateway.uz / demo1234)
python manage.py seed_demo

# Run the development server
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Docker

```bash
docker-compose up --build
```

The app will be available at http://localhost:8000.

## Project Structure

```
aigateway/
├── settings/          # base/dev/prod settings split
├── apps/
│   ├── accounts/      # Custom user model, signup/login
│   ├── orgs/          # Organizations, memberships, policies
│   ├── providers/     # Provider registry, models, credential encryption, adapters
│   ├── ai_gateway/    # AIRequest model, unified router
│   ├── prompt_templates/  # Saved prompt templates
│   ├── usage/         # UsageEvent model
│   ├── billing/       # Plans, subscriptions, invoices, payments
│   ├── audit/         # AuditLog
│   ├── web/           # Server-rendered pages (dashboard, playground, etc.)
│   └── api/           # DRF API endpoints
├── templates/         # Django HTML templates
└── static/            # Static assets (CSS, JS, images)
tests/
├── test_encryption.py     # Credential encryption tests
├── test_permissions.py    # RBAC/permissions tests
├── test_routing.py        # AI routing & fallback tests
└── test_usage.py          # Usage logging tests
```

## Pages

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/auth/signup/` | Sign up |
| `/auth/login/` | Sign in |
| `/onboarding/` | Create organization |
| `/app/` | Dashboard |
| `/app/playground/` | AI Playground |
| `/app/templates/` | Prompt templates |
| `/app/usage/` | Usage analytics + CSV export |
| `/app/providers/` | Provider & credential management |
| `/app/members/` | Team management |
| `/app/billing/` | Plans & invoices |
| `/app/settings/` | Org policies (caps, retention, mode) |
| `/legal/terms/` | Terms of Service |
| `/legal/privacy/` | Privacy Policy |

## API Endpoints

All API endpoints require authentication via session or org API token (`Authorization: Bearer <token>`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/generate` | Unified AI generation |
| GET | `/api/v1/usage` | List usage events |
| GET | `/api/v1/usage/export.csv` | Export usage CSV |
| GET/POST | `/api/v1/templates` | List/create prompt templates |
| GET/PUT/DELETE | `/api/v1/templates/<id>` | Template detail |

### Unified AI Generate

```json
POST /api/v1/ai/generate
{
  "task_type": "chat",
  "input": "Explain quantum computing in simple terms",
  "system": "You are a helpful teacher",
  "preferred_provider": "openai",
  "max_cost_usd": 0.20,
  "stream": false
}
```

**Response:**
```json
{
  "output_text": "...",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "units_in": 15,
  "units_out": 120,
  "total_units": 135,
  "cost_usd_estimate": "0.000097",
  "request_id": "uuid",
  "latency_ms": 1234
}
```

## Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-django factory-boy ruff

# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_encryption.py -v
python -m pytest tests/test_permissions.py -v
python -m pytest tests/test_routing.py -v
python -m pytest tests/test_usage.py -v
```

## Production Notes

- Set `DJANGO_SETTINGS_MODULE=aigateway.settings.prod`
- Use PostgreSQL (`DATABASE_URL`)
- Set a strong `SECRET_KEY` and `ENCRYPTION_KEY`
- Run with Gunicorn: `gunicorn aigateway.wsgi:application --bind 0.0.0.0:8000 --workers 3`
- WhiteNoise serves static files; run `python manage.py collectstatic`
- Optional: put Nginx in front for TLS termination

## License

This project is licensed under the MIT License.
