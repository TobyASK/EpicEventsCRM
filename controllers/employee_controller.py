from sqlalchemy.orm import Session
from models import Employee, Department
from utils import (
    hash_password,
    Permission,
    check_permission,
    log_employee_creation, log_employee_update, log_exception,
)
from typing import List, Optional


class EmployeeController:

    def __init__(self, db: Session):
        """Initialise le contrôleur des employés."""
        self.db = db

    def _require(self, current_user: dict, permission: str, message: str):
        """Valide une permission et lève une erreur si refusée."""
        if not check_permission(current_user.get('department'), permission):
            raise PermissionError(message)

    def _get_employee(self, employee_id: int) -> Optional[Employee]:
        """Récupère un employé par son identifiant."""
        return self.db.query(Employee).filter(Employee.id == employee_id).first()

    def create_employee(
        self,
        current_user: dict,
        employee_number: str,
        full_name: str,
        email: str,
        password: str,
        department: str
    ) -> Employee:
        """Crée un nouvel employé."""
        try:
            self._require(
                current_user,
                Permission.CREATE_EMPLOYEE,
                "Permission refusée pour créer un employé",
            )

            existing = self.db.query(Employee).filter(
                Employee.email == email).first()
            if existing:
                raise ValueError(
                    f"Un employé avec l'email {email} existe déjà")

            existing = self.db.query(Employee).filter(
                Employee.employee_number == employee_number).first()
            if existing:
                raise ValueError(
                    f"Le numéro d'employé {employee_number} "
                    "existe déjà")

            try:
                dept = Department(department)
            except ValueError:
                raise ValueError(f"Département invalide: {department}")

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

            log_employee_creation(email, department)

            return employee

        except Exception as e:
            self.db.rollback()
            log_exception(e, {"action": "create_employee", "email": email})
            raise

    def get_all_employees(self, current_user: dict) -> List[Employee]:
        """Liste tous les employés."""
        try:
            self._require(
                current_user,
                Permission.READ_EMPLOYEES,
                "Permission refusée pour lire les employés",
            )

            return self.db.query(Employee).all()

        except Exception as e:
            log_exception(e, {"action": "get_all_employees"})
            raise

    def get_employee_by_id(
        self, current_user: dict, employee_id: int
    ) -> Optional[Employee]:
        """Récupère un employé par ID avec contrôle d'accès."""
        try:
            self._require(
                current_user,
                Permission.READ_EMPLOYEES,
                "Permission refusée pour lire les employés",
            )
            return self._get_employee(employee_id)

        except Exception as e:
            log_exception(e, {
                "action": "get_employee_by_id",
                "employee_id": employee_id,
            })
            raise

    def get_employee_by_email(self, email: str) -> Optional[Employee]:
        """Récupère un employé via son email."""
        return self.db.query(Employee).filter(
            Employee.email == email).first()

    def update_employee(
        self,
        current_user: dict,
        employee_id: int,
        **kwargs
    ) -> Employee:
        """Met à jour un employé existant."""
        try:
            self._require(
                current_user,
                Permission.UPDATE_EMPLOYEE,
                "Permission refusée pour modifier un employé",
            )

            employee = self._get_employee(employee_id)
            if not employee:
                raise ValueError(f"Employé {employee_id} non trouvé")

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
        """Supprime un employé."""
        try:
            self._require(
                current_user,
                Permission.DELETE_EMPLOYEE,
                "Permission refusée pour supprimer un employé",
            )

            if employee_id == current_user.get('employee_id'):
                raise ValueError(
                    "Vous ne pouvez pas supprimer votre propre compte")

            employee = self._get_employee(employee_id)
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
        """Liste les employés d'un département."""
        try:
            self._require(
                current_user,
                Permission.READ_EMPLOYEES,
                "Permission refusée pour lire les employés",
            )

            dept = Department(department)
            return self.db.query(Employee).filter(
                Employee.department == dept).all()

        except Exception as e:
            log_exception(e, {
                "action": "get_employees_by_department",
                "department": department,
            })
            raise
