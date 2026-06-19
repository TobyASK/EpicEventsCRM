"""
Controller pour l'authentification
"""
from sqlalchemy.orm import Session
from controllers.employee_controller import EmployeeController
from utils.auth import (
    verify_password, create_jwt_token, save_token_to_file,
    load_token_from_file, decode_jwt_token, delete_token_file,
)
from utils.sentry_logger import log_exception
from typing import Optional


class AuthController:
    """Contrôleur pour gérer l'authentification"""

    def __init__(self, db: Session):
        self.db = db
        self.employee_controller = EmployeeController(db)

    def login(self, email: str, password: str) -> dict:
        """
        Authentifie un employé et retourne un token JWT

        Args:
            email: Email de l'employé
            password: Mot de passe

        Returns:
            Dictionnaire avec le token et les infos de l'employé

        Raises:
            ValueError: Si les identifiants sont incorrects
        """
        try:
            # Récupérer l'employé
            employee = self.employee_controller.get_employee_by_email(email)
            if not employee:
                raise ValueError("Email ou mot de passe incorrect")

            # Vérifier le mot de passe
            if not verify_password(password, employee.password_hash):
                raise ValueError("Email ou mot de passe incorrect")

            # Créer le token JWT
            token = create_jwt_token(
                employee.id,
                employee.email,
                employee.department.value
            )

            # Sauvegarder le token
            save_token_to_file(token)

            return {
                'token': token,
                'employee_id': employee.id,
                'email': employee.email,
                'full_name': employee.full_name,
                'department': employee.department.value
            }

        except Exception as e:
            log_exception(e, {"action": "login", "email": email})
            raise

    def logout(self):
        """
        Déconnecte l'utilisateur en supprimant le token
        """
        try:
            delete_token_file()
        except Exception as e:
            log_exception(e, {"action": "logout"})
            raise

    def get_current_user(self) -> Optional[dict]:
        """
        Récupère l'utilisateur actuellement authentifié

        Returns:
            Les informations de l'utilisateur ou None
        """
        try:
            # Charger le token
            token = load_token_from_file()
            if not token:
                return None

            # Décoder le token
            payload = decode_jwt_token(token)
            if not payload:
                # Token expiré ou invalide
                delete_token_file()
                return None

            return payload

        except Exception as e:
            log_exception(e, {"action": "get_current_user"})
            return None

    def require_auth(self) -> dict:
        """
        Vérifie qu'un utilisateur est authentifié

        Returns:
            Les informations de l'utilisateur

        Raises:
            PermissionError: Si l'utilisateur n'est pas authentifié
        """
        current_user = self.get_current_user()
        if not current_user:
            raise PermissionError(
                "Vous devez être authentifié pour effectuer cette action")
        return current_user
