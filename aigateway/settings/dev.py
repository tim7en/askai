from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Use SQLite for development if no DATABASE_URL
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),  # noqa: F405
}

# Console email
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use simple static storage in dev
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Auto-verify users in dev mode
AUTO_VERIFY_EMAIL = True
