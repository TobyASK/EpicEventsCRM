"""
Controller pour la gestion des employés
"""
from sqlalchemy.orm import Session
from models.employee import Employee, Department
from utils.auth import hash_password
from utils.permissions import Permission, check_permission
from utils.sentry_logger import (
    log_employee_creation, log_employee_update, log_exception,
)
from typing import List, Optional


class EmployeeController:
    """Contrôleur pour gérer les opérations CRUD sur les employés"""

    def __init__(self, db: Session):
        self.db = db

    def create_employee(
        self,
        current_user: dict,
        employee_number: str,
        full_name: str,
        email: str,
        password: str,
        department: str
    ) -> Employee:
        """
        Crée un nouvel employé

        Args:
            current_user: L'utilisateur authentifié
            employee_number: Numéro d'employé
            full_name: Nom complet
            email: Email
            password: Mot de passe
            department: Département

        Returns:
            L'employé créé

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission
            ValueError: Si les données sont invalides
        """
        try:
            # Vérifier les permissions
            dept_user = current_user.get('department')
            if not check_permission(dept_user, Permission.CREATE_EMPLOYEE):
                raise PermissionError(
                    "Permission refusée pour créer un employé")

            # Vérifier que l'email n'existe pas déjà
            existing = self.db.query(Employee).filter(
                Employee.email == email).first()
            if existing:
                raise ValueError(
                    f"Un employé avec l'email {email} existe déjà")

            # Vérifier que le numéro d'employé n'existe pas
            existing = self.db.query(Employee).filter(
                Employee.employee_number == employee_number).first()
            if existing:
                raise ValueError(
                    f"Le numéro d'employé {employee_number} "
                    "existe déjà")

            # Valider le département
            try:
                dept = Department(department)
            except ValueError:
                raise ValueError(f"Département invalide: {department}")

            # Créer l'employé
            employee = Employee(
                employee_number=employee_number,
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                department=dept
            )

            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)

            # Journaliser
            log_employee_creation(email, department)

            return employee

        except Exception as e:
            self.db.rollback()
            log_exception(e, {"action": "create_employee", "email": email})
            raise

    def get_all_employees(self, current_user: dict) -> List[Employee]:
        """
        Récupère tous les employés

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des employés
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_EMPLOYEES):
                raise PermissionError(
                    "Permission refusée pour lire les employés")

            return self.db.query(Employee).all()

        except Exception as e:
            log_exception(e, {"action": "get_all_employees"})
            raise

    def get_employee_by_id(
        self, current_user: dict, employee_id: int
    ) -> Optional[Employee]:
        """
        Récupère un employé par son ID

        Args:
            current_user: L'utilisateur authentifié
            employee_id: ID de l'employé

        Returns:
            L'employé ou None
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_EMPLOYEES):
                raise PermissionError(
                    "Permission refusée pour lire les employés")

            return self.db.query(Employee).filter(
                Employee.id == employee_id).first()

        except Exception as e:
            log_exception(e, {
                "action": "get_employee_by_id",
                "employee_id": employee_id,
            })
            raise

    def get_employee_by_email(self, email: str) -> Optional[Employee]:
        """
        Récupère un employé par son email (pour l'authentification)

        Args:
            email: Email de l'employé

        Returns:
            L'employé ou None
        """
        return self.db.query(Employee).filter(
            Employee.email == email).first()

    def update_employee(
        self,
        current_user: dict,
        employee_id: int,
        **kwargs
    ) -> Employee:
        """
        Met à jour un employé

        Args:
            current_user: L'utilisateur authentifié
            employee_id: ID de l'employé à modifier
            **kwargs: Champs à mettre à jour

        Returns:
            L'employé modifié
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.UPDATE_EMPLOYEE):
                raise PermissionError(
                    "Permission refusée pour modifier un employé")

            employee = self.db.query(Employee).filter(
                Employee.id == employee_id).first()
            if not employee:
                raise ValueError(f"Employé {employee_id} non trouvé")

            # Mettre à jour les champs
            if 'full_name' in kwargs:
                employee.full_name = kwargs['full_name']
            if 'email' in kwargs:
                employee.email = kwargs['email']
            if 'department' in kwargs:
                employee.department = Department(kwargs['department'])
            if 'password' in kwargs:
                employee.password_hash = hash_password(kwargs['password'])

            self.db.commit()
            self.db.refresh(employee)

            # Journaliser
            log_employee_update(employee.email, current_user.get('email'))

            return employee

        except Exception as e:
            self.db.rollback()
            log_exception(e, {
                "action": "update_employee",
                "employee_id": employee_id,
            })
            raise

    def delete_employee(self, current_user: dict, employee_id: int) -> None:
        """
        Supprime un employé.

        Args:
            current_user: L'utilisateur authentifié
            employee_id: ID de l'employé à supprimer

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission
            ValueError: Si l'employé n'existe pas ou tentative
                d'auto-suppression
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.DELETE_EMPLOYEE):
                raise PermissionError(
                    "Permission refusée pour supprimer un employé")

            if employee_id == current_user.get('employee_id'):
                raise ValueError(
                    "Vous ne pouvez pas supprimer votre propre compte")

            employee = self.db.query(Employee).filter(
                Employee.id == employee_id).first()
            if not employee:
                raise ValueError(f"Employé {employee_id} non trouvé")

            self.db.delete(employee)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            log_exception(e, {
                "action": "delete_employee",
                "employee_id": employee_id,
            })
            raise

    def get_employees_by_department(
        self, current_user: dict, department: str
    ) -> List[Employee]:
        """
        Récupère les employés d'un département

        Args:
            current_user: L'utilisateur authentifié
            department: Le département

        Returns:
            Liste des employés du département
        """
        try:
            dept_user = current_user.get('department')
            if not check_permission(dept_user, Permission.READ_EMPLOYEES):
                raise PermissionError(
                    "Permission refusée pour lire les employés")

            dept = Department(department)
            return self.db.query(Employee).filter(
                Employee.department == dept).all()

        except Exception as e:
            log_exception(e, {
                "action": "get_employees_by_department",
                "department": department,
            })
            raise
