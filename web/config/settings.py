import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = ["*"]

# URL de la API (el frontend NO se conecta a la base de datos)
API_URL = os.environ.get("API_URL", "http://api:5000")

INSTALLED_APPS = [
    "django.contrib.messages",
    "ordenes",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {}  # sin base de datos propia: todo pasa por la API
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Tegucigalpa"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
