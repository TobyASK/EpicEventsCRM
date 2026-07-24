import sentry_sdk
from config import (
    SENTRY_DSN,
    SENTRY_ENVIRONMENT,
    SENTRY_TRACES_SAMPLE_RATE,
    APP_NAME,
    APP_VERSION,
)


def init_sentry():
    """Initialise Sentry si un DSN est configuré."""
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            release=f"{APP_NAME}@{APP_VERSION}",
            environment=SENTRY_ENVIRONMENT,
        )


def log_employee_creation(employee_email: str, department: str):
    """Envoie un log Sentry lors de la création d'un employé."""
    sentry_sdk.capture_message(
        f"Création d'employé: {employee_email} ({department})",
        level="info"
    )


def log_employee_update(employee_email: str, updated_by: str):
    """Envoie un log Sentry lors de la modification d'un employé."""
    sentry_sdk.capture_message(
        f"Modification d'employé: {employee_email} par {updated_by}",
        level="info"
    )


def log_contract_signed(contract_number: str, client_name: str):
    """Envoie un log Sentry lors de la signature d'un contrat."""
    sentry_sdk.capture_message(
        f"Signature de contrat: {contract_number} pour {client_name}",
        level="info"
    )


def log_exception(exception: Exception, context: dict = None):
    """Envoie une exception et son contexte à Sentry."""
    if context:
        sentry_sdk.set_context("custom", context)
    sentry_sdk.capture_exception(exception)
