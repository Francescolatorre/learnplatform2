import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGIN_URL = "/nonexistent/"  # Prevent Django from redirecting to login for Swagger
LOGOUT_REDIRECT_URL = "/"  # Optional: Set a default logout redirect

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # Ensure this directory exists
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # For production use

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

ROOT_URLCONF = "learningplatform_backend.urls"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file_debug": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/debug.log"),
            "formatter": "verbose",
        },
        "file_api": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/api.log"),
            "formatter": "verbose",
        },
        "file_auth": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/auth.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": True,
        },
        "core.views": {
            "handlers": ["file_debug", "file_api"],
            "level": "DEBUG",
            "propagate": False,
        },
        "core.permissions": {
            "handlers": ["file_auth"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",  # Add CORS headers app
    "learningplatform_backend",  # Ensure this app is listed
    "core"  # Ensure the core app is listed here
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "learningplatform_backend.middleware.middleware.RequestLoggingMiddleware",
    "learningplatform_backend.middleware.middleware.DebugLoggingMiddleware",
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Allow requests from the frontend
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # Use only JWT authentication
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # Allow unrestricted access by default
    ],
    "EXCEPTION_HANDLER": "learningplatform_backend.core.exception_handler.custom_exception_handler",
}


AUTH_USER_MODEL = 'core.User'  # Ensure this is correctly set
