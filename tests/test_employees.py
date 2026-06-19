"""
Tests unitaires et d'intégration — EmployeeController + utils/auth.
"""
import pytest
from models.employee import Employee, Department
from utils.auth import (
    hash_password, verify_password, create_jwt_token, decode_jwt_token,
)
from controllers.employee_controller import EmployeeController


# ── utils/auth ──────────────────────────────────────────────────────────

def test_hash_password_not_plaintext():
    """Le hash ne doit pas être identique au mot de passe en clair."""
    pw = "secret_123"
    assert hash_password(pw) != pw


def test_hash_password_argon2_prefix():
    """Argon2 produit un hash reconnaissable à son préfixe $argon2."""
    assert hash_password("pass").startswith("$argon2")


def test_verify_password_correct():
    """Un mot de passe correct doit être vérifié avec succès."""
    pw = "test_password_123"
    assert verify_password(pw, hash_password(pw)) is True


def test_verify_password_wrong():
    """Un mauvais mot de passe doit retourner False."""
    assert verify_password("wrong", hash_password("right")) is False


def test_jwt_roundtrip():
    """Un token JWT encodé puis décodé doit contenir le bon payload."""
    token = create_jwt_token(42, "user@test.com", "gestion")
    payload = decode_jwt_token(token)
    assert payload is not None
    assert payload["employee_id"] == 42
    assert payload["department"] == "gestion"


def test_jwt_invalid_token():
    """Un token falsifié doit retourner None."""
    assert decode_jwt_token("not.a.valid.token") is None


# ── EmployeeController ──────────────────────────────────────────────────

def test_create_employee(db_session, admin_user):
    """Gestion peut créer un employé avec des données valides."""
    ctrl = EmployeeController(db_session)
    emp = ctrl.create_employee(
        admin_user, "EMP001", "John Doe", "john@test.com", "pass123",
        "commercial")
    assert emp.id is not None
    assert emp.full_name == "John Doe"
    assert emp.department == Department.COMMERCIAL


def test_create_employee_duplicate_email(db_session, admin_user):
    """La création avec un email existant lève ValueError."""
    ctrl = EmployeeController(db_session)
    ctrl.create_employee(
        admin_user, "EMP001", "John", "dup@test.com", "pass",
        "commercial")
    with pytest.raises(ValueError, match="existe déjà"):
        ctrl.create_employee(
            admin_user, "EMP002", "Jane", "dup@test.com", "pass",
            "support")


def test_create_employee_duplicate_number(db_session, admin_user):
    """La création avec un numéro d'employé existant lève ValueError."""
    ctrl = EmployeeController(db_session)
    ctrl.create_employee(
        admin_user, "SAME", "Alice", "alice@test.com", "pass",
        "commercial")
    with pytest.raises(ValueError, match="existe déjà"):
        ctrl.create_employee(
            admin_user, "SAME", "Bob", "bob@test.com", "pass",
            "support")


def test_create_employee_invalid_department(db_session, admin_user):
    """Un département inexistant lève ValueError."""
    ctrl = EmployeeController(db_session)
    with pytest.raises(ValueError, match="Département invalide"):
        ctrl.create_employee(
            admin_user, "X", "X", "x@x.com", "pass", "marketing")


def test_commercial_cannot_create_employee(db_session, commercial_user):
    """Un commercial ne peut pas créer un employé."""
    ctrl = EmployeeController(db_session)
    with pytest.raises(PermissionError):
        ctrl.create_employee(
            commercial_user, "E", "E", "e@e.com", "pass", "commercial")


def test_get_all_employees(db_session, admin_user):
    """Gestion peut lister tous les employés."""
    ctrl = EmployeeController(db_session)
    for i in range(3):
        ctrl.create_employee(
            admin_user, f"E{i}", f"Emp {i}", f"e{i}@test.com", "p",
            "commercial")
    # +1 pour l'admin créé dans la fixture admin_user
    assert len(ctrl.get_all_employees(admin_user)) >= 4


def test_get_all_employees_permission_denied(db_session, commercial_user):
    """Un commercial ne peut pas lister les employés."""
    ctrl = EmployeeController(db_session)
    with pytest.raises(PermissionError):
        ctrl.get_all_employees(commercial_user)


def test_update_employee(db_session, admin_user):
    """Gestion peut modifier le nom d'un employé."""
    ctrl = EmployeeController(db_session)
    emp = ctrl.create_employee(
        admin_user, "U1", "Before", "before@test.com", "p", "commercial")
    updated = ctrl.update_employee(admin_user, emp.id, full_name="After")
    assert updated.full_name == "After"


def test_delete_employee(db_session, admin_user):
    """Gestion peut supprimer un employé qui n'est pas soi-même."""
    ctrl = EmployeeController(db_session)
    emp = ctrl.create_employee(
        admin_user, "D1", "ToDelete", "del@test.com", "p", "support")
    ctrl.delete_employee(admin_user, emp.id)
    assert db_session.query(Employee).filter(
        Employee.id == emp.id).first() is None


def test_delete_own_account_forbidden(db_session, admin_user):
    """Un employé ne peut pas supprimer son propre compte."""
    ctrl = EmployeeController(db_session)
    with pytest.raises(ValueError, match="propre compte"):
        ctrl.delete_employee(admin_user, admin_user["employee_id"])


def test_delete_employee_not_found(db_session, admin_user):
    """Supprimer un ID inexistant lève ValueError."""
    ctrl = EmployeeController(db_session)
    with pytest.raises(ValueError, match="non trouvé"):
        ctrl.delete_employee(admin_user, 99999)
