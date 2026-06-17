# maps_scraper_admin/settings.py
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Security - SETELAH SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-demo-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

if not DEBUG:
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True)
        print("✅ Playwright browsers installed")
    except Exception as e:
        print(f"⚠️ Could not install Playwright: {e}")

#HEADLESS = os.environ.get('DJANGO_HEADLESS', 'True') == 'True'

# ============ PERBAIKAN CSRF ============
ALLOWED_HOSTS = [
    '*',  # Untuk Railway/Render
    'localhost',
    '127.0.0.1',
    '.onrender.com',  # Untuk Render
    '.railway.app',   # Untuk Railway
    '.up.railway.app',
]

# CSRF Settings - TAMBAHKAN INI!
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.railway.app',
    'https://*.up.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# CSRF Cookie Settings
CSRF_COOKIE_SECURE = False # not DEBUG
CSRF_COOKIE_HTTPONLY = False  # Biarkan False untuk development
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# Session Settings
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'

# Security Middleware
SECURE_SSL_REDIRECT = False # not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# =========================================

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'scraper_data',
    'import_export',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # PASTIKAN INI ADA!
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'maps_scraper_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'maps_scraper_admin.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
