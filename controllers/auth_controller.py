from sqlalchemy.orm import Session
from controllers.employee_controller import EmployeeController
from models import Employee
from utils import (
    verify_password, create_jwt_token, save_token_to_file,
    load_token_from_file, decode_jwt_token, delete_token_file,
)
from utils import log_exception
from typing import Optional


class AuthController:

    def __init__(self, db: Session):
        """Initialise le contrôleur d'authentification."""
        self.db = db
        self.employee_controller = EmployeeController(db)

    def login(self, email: str, password: str) -> dict:
        """Authentifie un employé et crée sa session JWT."""
        try:
            employee = self.employee_controller.get_employee_by_email(email)
            if not employee:
                raise ValueError("Email ou mot de passe incorrect")

            if not verify_password(password, employee.password_hash):
                raise ValueError("Email ou mot de passe incorrect")

            token = create_jwt_token(
                employee.id,
                employee.email,
                employee.department.value
            )

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
        """Termine la session locale courante."""
        try:
            delete_token_file()
        except Exception as e:
            log_exception(e, {"action": "logout"})
            raise

    @staticmethod
    def to_user_context(employee: Employee) -> dict:
        """Construit un contexte utilisateur compatible contrôleurs."""
        return {
            'employee_id': employee.id,
            'email': employee.email,
            'full_name': employee.full_name,
            'department': employee.department.value,
        }

    def get_current_user(self) -> Optional[Employee]:
        """Retourne l'employé courant à partir du token local."""
        try:
            token = load_token_from_file()
            if not token:
                return None

            payload = decode_jwt_token(token)
            if not payload:
                delete_token_file()
                return None

            employee_id = payload.get('employee_id')
            employee_email = payload.get('email')
            if not employee_id or not employee_email:
                delete_token_file()
                return None

            employee = self.employee_controller.get_employee_by_email(employee_email)
            if not employee or employee.id != employee_id:
                delete_token_file()
                return None

            return employee

        except Exception as e:
            log_exception(e, {"action": "get_current_user"})
            return None

    def require_auth(self) -> dict:
        """Exige une session authentifiée et renvoie le contexte utilisateur."""
        employee = self.get_current_user()
        if not employee:
            raise PermissionError(
                "Vous devez être authentifié pour effectuer cette action")
        return self.to_user_context(employee)
