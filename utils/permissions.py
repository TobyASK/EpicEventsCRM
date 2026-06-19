"""
Gestion des permissions et autorisations
"""
from models.employee import Department


class Permission:
    """Classe pour définir les permissions disponibles"""

    # Permissions sur les clients
    CREATE_CLIENT = "create_client"
    READ_ALL_CLIENTS = "read_all_clients"
    READ_OWN_CLIENTS = "read_own_clients"
    UPDATE_OWN_CLIENTS = "update_own_clients"

    # Permissions sur les contrats
    CREATE_CONTRACT = "create_contract"
    READ_ALL_CONTRACTS = "read_all_contracts"
    UPDATE_CONTRACT = "update_contract"         # Gestion : tous les contrats
    UPDATE_OWN_CONTRACTS = "update_own_contracts"  # Commercial : ses contrats
    SIGN_CONTRACT = "sign_contract"

    # Permissions sur les événements
    CREATE_EVENT = "create_event"
    READ_ALL_EVENTS = "read_all_events"
    READ_OWN_EVENTS = "read_own_events"
    UPDATE_OWN_EVENTS = "update_own_events"
    ASSIGN_SUPPORT = "assign_support"

    # Permissions sur les employés
    CREATE_EMPLOYEE = "create_employee"
    READ_EMPLOYEES = "read_employees"
    UPDATE_EMPLOYEE = "update_employee"
    DELETE_EMPLOYEE = "delete_employee"


# CDC : tous les collaborateurs ont accès en lecture à tout
_READ_ALL = [
    Permission.READ_ALL_CLIENTS,
    Permission.READ_ALL_CONTRACTS,
    Permission.READ_ALL_EVENTS,
]

DEPARTMENT_PERMISSIONS = {
    Department.COMMERCIAL: _READ_ALL + [
        # Clients : créer + modifier les siens
        Permission.CREATE_CLIENT,
        Permission.READ_OWN_CLIENTS,
        Permission.UPDATE_OWN_CLIENTS,
        # Contrats : modifier ceux de ses clients
        Permission.UPDATE_OWN_CONTRACTS,
        # Événements : créer (après contrat signé, pour ses clients)
        Permission.CREATE_EVENT,
    ],
    Department.SUPPORT: _READ_ALL + [
        # Événements : voir et modifier les siens
        Permission.READ_OWN_EVENTS,
        Permission.UPDATE_OWN_EVENTS,
    ],
    Department.GESTION: _READ_ALL + [
        # Employés
        Permission.CREATE_EMPLOYEE,
        Permission.READ_EMPLOYEES,
        Permission.UPDATE_EMPLOYEE,
        Permission.DELETE_EMPLOYEE,
        # Contrats
        Permission.CREATE_CONTRACT,
        Permission.UPDATE_CONTRACT,
        Permission.SIGN_CONTRACT,
        # Événements
        Permission.ASSIGN_SUPPORT,
    ]
}


def has_permission(department: Department, permission: str) -> bool:
    """
    Vérifie si un département a une permission donnée

    Args:
        department: Le département à vérifier
        permission: La permission requise

    Returns:
        True si le département a la permission
    """
    return permission in DEPARTMENT_PERMISSIONS.get(department, [])


def check_permission(
    employee_department: str,
    required_permission: str,
) -> bool:
    """
    Vérifie si un employé a une permission

    Args:
        employee_department: Le département de l'employé (string)
        required_permission: La permission requise

    Returns:
        True si l'employé a la permission
    """
    try:
        dept = Department(employee_department)
        return has_permission(dept, required_permission)
    except ValueError:
        return False


def require_permission(required_permission: str):
    """
    Décorateur pour vérifier les permissions avant l'exécution d'une fonction

    Args:
        required_permission: La permission requise
    """
    def decorator(func):
        def wrapper(current_user, *args, **kwargs):
            if not check_permission(
                current_user.get('department'),
                required_permission,
            ):
                raise PermissionError(
                    f"Permission refusée: {required_permission} requise"
                )
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator
