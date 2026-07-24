import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./epicevents.db')

JWT_SECRET_KEY = os.getenv(
    'JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
JWT_ALGORITHM = 'HS256'

AUTH_TOKEN_FILE = os.getenv(
    'AUTH_TOKEN_FILE', str(Path.home() / '.epicevents_auth_token'))

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'production')
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '1.0'))

APP_NAME = "Epic Events CRM"
APP_VERSION = "1.0.0"

DEFAULT_ADMIN_EMPLOYEE_NUMBER = os.getenv('DEFAULT_ADMIN_EMPLOYEE_NUMBER', 'ADMIN001')
DEFAULT_ADMIN_FULL_NAME = os.getenv('DEFAULT_ADMIN_FULL_NAME', 'Administrateur')
DEFAULT_ADMIN_EMAIL = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@epicevents.com')
DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
