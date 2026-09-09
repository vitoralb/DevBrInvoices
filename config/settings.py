import os
import datetime
from pathlib import Path
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False") == "True"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-insecure-key-only-for-local-debugging"
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY environment variable must be set in production."
        )

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"] if DEBUG else ["localhost", "127.0.0.1"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_htmx",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "core.middleware.RequireCompanySettingsMiddleware",
]

# Security headers for production
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.company_settings",
                "core.context_processors.project_settings",
            ],
        },
    },
]

PROJECT_NAME = os.environ.get("PROJECT_NAME", "DevBrInvoices")

WSGI_APPLICATION = "config.wsgi.application"

# Database configuration
if os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "notas"),
            "USER": os.environ.get("POSTGRES_USER", "notas"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", "db"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
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

# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (PDFs, XMLs)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Authentication URLs
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "login"

# Email Configuration (Django 6+ MAILERS)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", os.environ.get("EMAIL_HOST_USER", "")
)
MAILERS = {
    "default": {
        "BACKEND": os.environ.get(
            "EMAIL_BACKEND",
            (
                "django.core.mail.backends.console.EmailBackend"
                if DEBUG
                else "django.core.mail.backends.smtp.EmailBackend"
            ),
        ),
        "OPTIONS": {
            "host": os.environ.get("EMAIL_HOST", "smtp.gmail.com"),
            "port": int(os.environ.get("EMAIL_PORT", 587)),
            "use_tls": os.environ.get("EMAIL_USE_TLS", "True") == "True",
            "username": os.environ.get("EMAIL_HOST_USER", ""),
            "password": os.environ.get("EMAIL_HOST_PASSWORD", ""),
        },
    },
}

# NFE (Nota Fiscal Eletrônica) Configuration

# Feature Flag: When to start accumulating CPP in Fator R calculations (YYYY-MM-DD)
CPP_ACCUMULATION_START_DATE = os.environ.get("CPP_ACCUMULATION_START_DATE", None)
if CPP_ACCUMULATION_START_DATE:
    try:
        CPP_ACCUMULATION_START_DATE = datetime.datetime.strptime(
            CPP_ACCUMULATION_START_DATE, "%Y-%m-%d"
        ).date()
    except ValueError:
        CPP_ACCUMULATION_START_DATE = None

# Celery Configuration
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    "process_daily_invoices": {
        "task": "core.tasks.process_daily_invoices_task",
        "schedule": crontab(minute=0, hour="*"),
    },
}

# Structured Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} [{name}:{lineno}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
