"""
Paramètres généraux de l'application
"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def _int_env(name: str, default: int) -> int:
    """Lit une variable d'environnement entière avec fallback sûr."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# JWT Configuration
JWT_SECRET_KEY = os.getenv(
    'JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = _int_env('JWT_EXPIRATION_HOURS', 8)

# Session token file
AUTH_TOKEN_FILE = os.getenv(
    'AUTH_TOKEN_FILE',
    str(Path.home() / '.epicevents_auth_token')
)

# Sentry Configuration
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Application
APP_NAME = "Epic Events CRM"
APP_VERSION = "1.0.0"
