"""
Configuration et initialisation de Sentry pour la journalisation
"""
import sentry_sdk
from config.settings import SENTRY_DSN, APP_NAME, APP_VERSION


def init_sentry():
    """
    Initialise Sentry pour la journalisation des erreurs et événements
    """
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0,
            release=f"{APP_NAME}@{APP_VERSION}",
            environment="production"
        )


def log_employee_creation(employee_email: str, department: str):
    """
    Journalise la création d'un employé

    Args:
        employee_email: Email de l'employé créé
        department: Département de l'employé
    """
    sentry_sdk.capture_message(
        f"Création d'employé: {employee_email} ({department})",
        level="info"
    )


def log_employee_update(employee_email: str, updated_by: str):
    """
    Journalise la modification d'un employé

    Args:
        employee_email: Email de l'employé modifié
        updated_by: Email de l'utilisateur qui a fait la modification
    """
    sentry_sdk.capture_message(
        f"Modification d'employé: {employee_email} par {updated_by}",
        level="info"
    )


def log_contract_signed(contract_number: str, client_name: str):
    """
    Journalise la signature d'un contrat

    Args:
        contract_number: Numéro du contrat
        client_name: Nom du client
    """
    sentry_sdk.capture_message(
        f"Signature de contrat: {contract_number} pour {client_name}",
        level="info"
    )


def log_exception(exception: Exception, context: dict = None):
    """
    Journalise une exception

    Args:
        exception: L'exception à journaliser
        context: Contexte additionnel
    """
    if context:
        sentry_sdk.set_context("custom", context)
    sentry_sdk.capture_exception(exception)
