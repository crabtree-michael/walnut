"""Django settings for elk_api project."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dummy-secret-key-change-me")

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS: List[str] = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host]
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "hazards",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "elk_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "elk_api.wsgi.application"

database_url = os.getenv("DATABASE_URL")
DATABASES = {
    'default': dj_database_url.config(
        default=f'postgres://{os.environ.get("DB_USER", "user")}:{os.environ.get("DB_PASSWORD", "password")}@{os.environ.get("DB_HOST", "localhost")}:{os.environ.get("DB_PORT", "5432")}/{os.environ.get("DB_NAME", "mydatabase")}'
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
infra_domain = os.getenv("INFRA_API_DOMAIN")
if infra_domain:
    CORS_ALLOWED_ORIGINS.append(f"https://{infra_domain}")

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}


def require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise ImproperlyConfigured(f"Missing required environment variable: {var_name}")
    return value
