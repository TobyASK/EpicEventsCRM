"""
Paramètres généraux de l'application
"""
import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY = os.getenv(
    'JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 8

# Sentry Configuration
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Application
APP_NAME = "Epic Events CRM"
APP_VERSION = "1.0.0"
