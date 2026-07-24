from models import Department


class Permission:

    CREATE_CLIENT = "create_client"
    READ_ALL_CLIENTS = "read_all_clients"
    READ_OWN_CLIENTS = "read_own_clients"
    UPDATE_OWN_CLIENTS = "update_own_clients"

    CREATE_CONTRACT = "create_contract"
    READ_ALL_CONTRACTS = "read_all_contracts"
    UPDATE_CONTRACT = "update_contract"         # Gestion : tous les contrats
    UPDATE_OWN_CONTRACTS = "update_own_contracts"  # Commercial : ses contrats
    SIGN_CONTRACT = "sign_contract"

    CREATE_EVENT = "create_event"
    READ_ALL_EVENTS = "read_all_events"
    READ_OWN_EVENTS = "read_own_events"
    UPDATE_OWN_EVENTS = "update_own_events"
    ASSIGN_SUPPORT = "assign_support"

    CREATE_EMPLOYEE = "create_employee"
    READ_EMPLOYEES = "read_employees"
    UPDATE_EMPLOYEE = "update_employee"
    DELETE_EMPLOYEE = "delete_employee"


_READ_ALL = [
    Permission.READ_ALL_CLIENTS,
    Permission.READ_ALL_CONTRACTS,
    Permission.READ_ALL_EVENTS,
]

DEPARTMENT_PERMISSIONS = {
    Department.COMMERCIAL: _READ_ALL + [
        Permission.CREATE_CLIENT,
        Permission.READ_OWN_CLIENTS,
        Permission.UPDATE_OWN_CLIENTS,
        Permission.UPDATE_OWN_CONTRACTS,
        Permission.CREATE_EVENT,
    ],
    Department.SUPPORT: _READ_ALL + [
        Permission.READ_OWN_EVENTS,
        Permission.UPDATE_OWN_EVENTS,
    ],
    Department.GESTION: _READ_ALL + [
        Permission.CREATE_EMPLOYEE,
        Permission.READ_EMPLOYEES,
        Permission.UPDATE_EMPLOYEE,
        Permission.DELETE_EMPLOYEE,
        Permission.CREATE_CONTRACT,
        Permission.UPDATE_CONTRACT,
        Permission.SIGN_CONTRACT,
        Permission.ASSIGN_SUPPORT,
    ]
}


def has_permission(department: Department, permission: str) -> bool:
    """Vérifie si une permission est autorisée pour un département."""
    return permission in DEPARTMENT_PERMISSIONS.get(department, [])


def check_permission(
    employee_department: str,
    required_permission: str,
) -> bool:
    """Vérifie si un département possède une permission donnée."""
    try:
        dept = Department(employee_department)
        return has_permission(dept, required_permission)
    except ValueError:
        return False
