"""
Tests unitaires — système de permissions (utils/permissions.py).
"""
from utils.permissions import Permission, check_permission, has_permission
from models.employee import Department


# ── has_permission / check_permission ───────────────────────────────────

class TestCommercialPermissions:
    dept = "commercial"

    def test_can_read_all_clients(self):
        assert check_permission(self.dept, Permission.READ_ALL_CLIENTS)

    def test_can_read_all_contracts(self):
        assert check_permission(self.dept, Permission.READ_ALL_CONTRACTS)

    def test_can_read_all_events(self):
        assert check_permission(self.dept, Permission.READ_ALL_EVENTS)

    def test_can_create_client(self):
        assert check_permission(self.dept, Permission.CREATE_CLIENT)

    def test_can_update_own_clients(self):
        assert check_permission(self.dept, Permission.UPDATE_OWN_CLIENTS)

    def test_can_update_own_contracts(self):
        assert check_permission(self.dept, Permission.UPDATE_OWN_CONTRACTS)

    def test_can_create_event(self):
        assert check_permission(self.dept, Permission.CREATE_EVENT)

    def test_cannot_create_contract(self):
        assert not check_permission(self.dept, Permission.CREATE_CONTRACT)

    def test_cannot_sign_contract(self):
        assert not check_permission(self.dept, Permission.SIGN_CONTRACT)

    def test_cannot_create_employee(self):
        assert not check_permission(self.dept, Permission.CREATE_EMPLOYEE)

    def test_cannot_delete_employee(self):
        assert not check_permission(self.dept, Permission.DELETE_EMPLOYEE)

    def test_cannot_assign_support(self):
        assert not check_permission(self.dept, Permission.ASSIGN_SUPPORT)


class TestSupportPermissions:
    dept = "support"

    def test_can_read_all_clients(self):
        assert check_permission(self.dept, Permission.READ_ALL_CLIENTS)

    def test_can_read_all_contracts(self):
        assert check_permission(self.dept, Permission.READ_ALL_CONTRACTS)

    def test_can_read_all_events(self):
        assert check_permission(self.dept, Permission.READ_ALL_EVENTS)

    def test_can_read_own_events(self):
        assert check_permission(self.dept, Permission.READ_OWN_EVENTS)

    def test_can_update_own_events(self):
        assert check_permission(self.dept, Permission.UPDATE_OWN_EVENTS)

    def test_cannot_create_client(self):
        assert not check_permission(self.dept, Permission.CREATE_CLIENT)

    def test_cannot_create_event(self):
        assert not check_permission(self.dept, Permission.CREATE_EVENT)

    def test_cannot_create_contract(self):
        assert not check_permission(self.dept, Permission.CREATE_CONTRACT)

    def test_cannot_sign_contract(self):
        assert not check_permission(self.dept, Permission.SIGN_CONTRACT)


class TestGestionPermissions:
    dept = "gestion"

    def test_can_read_all_clients(self):
        assert check_permission(self.dept, Permission.READ_ALL_CLIENTS)

    def test_can_read_all_contracts(self):
        assert check_permission(self.dept, Permission.READ_ALL_CONTRACTS)

    def test_can_read_all_events(self):
        assert check_permission(self.dept, Permission.READ_ALL_EVENTS)

    def test_can_create_employee(self):
        assert check_permission(self.dept, Permission.CREATE_EMPLOYEE)

    def test_can_read_employees(self):
        assert check_permission(self.dept, Permission.READ_EMPLOYEES)

    def test_can_update_employee(self):
        assert check_permission(self.dept, Permission.UPDATE_EMPLOYEE)

    def test_can_delete_employee(self):
        assert check_permission(self.dept, Permission.DELETE_EMPLOYEE)

    def test_can_create_contract(self):
        assert check_permission(self.dept, Permission.CREATE_CONTRACT)

    def test_can_update_contract(self):
        assert check_permission(self.dept, Permission.UPDATE_CONTRACT)

    def test_can_sign_contract(self):
        assert check_permission(self.dept, Permission.SIGN_CONTRACT)

    def test_can_assign_support(self):
        assert check_permission(self.dept, Permission.ASSIGN_SUPPORT)

    def test_cannot_create_client(self):
        assert not check_permission(self.dept, Permission.CREATE_CLIENT)

    def test_cannot_create_event(self):
        assert not check_permission(self.dept, Permission.CREATE_EVENT)


# ── Cas limites ─────────────────────────────────────────────────────────

def test_unknown_department_returns_false():
    """Un département inconnu ne doit donner aucune permission."""
    assert check_permission("superadmin", Permission.CREATE_CLIENT) is False
    assert check_permission("", Permission.READ_ALL_EVENTS) is False
    assert check_permission(None, Permission.DELETE_EMPLOYEE) is False


def test_has_permission_with_enum():
    """has_permission fonctionne directement avec l'enum Department."""
    assert has_permission(
        Department.GESTION, Permission.SIGN_CONTRACT) is True
    assert has_permission(
        Department.COMMERCIAL, Permission.SIGN_CONTRACT) is False
