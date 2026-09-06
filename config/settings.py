"""
Minimal Django settings for the initial project scaffold (backlog task 1).

Deliberately app-less and database-less: this is only enough to boot Django and
run a smoke test. The settings split (base/dev/prod), PostgreSQL, Docker, and the
project apps arrive in later tasks.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Dev-only placeholder; task 2 moves this to the environment.
SECRET_KEY = "django-insecure-scaffold-only-replace-in-task-2"

DEBUG = True

ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# No database yet (task 1). PostgreSQL is wired up in task 2 / task 3.
DATABASES: dict[str, dict] = {}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
