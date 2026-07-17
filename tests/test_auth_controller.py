"""
Tests unitaires — AuthController et persistance du token.
"""
from controllers.auth_controller import AuthController
from models.employee import Employee, Department
from utils.auth import (
    create_jwt_token, save_token_to_file, load_token_from_file,
    delete_token_file,
)
from utils.auth import hash_password


def test_get_current_user_returns_employee(db_session, monkeypatch):
    """get_current_user retourne bien un Employee valide."""
    emp = Employee(
        employee_number="AUTH001",
        full_name="Auth User",
        email="auth@test.com",
        password_hash=hash_password("pass"),
        department=Department.GESTION,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)

    token = create_jwt_token(emp.id, emp.email, emp.department.value)
    monkeypatch.setattr(
        "controllers.auth_controller.load_token_from_file",
        lambda: token
    )

    ctrl = AuthController(db_session)
    current_user = ctrl.get_current_user()
    assert current_user is not None
    assert current_user.id == emp.id
    assert current_user.email == emp.email


def test_get_current_user_deletes_token_for_unknown_employee(
    db_session, monkeypatch
):
    """Un token valide pour un employé supprimé doit être invalidé."""
    token = create_jwt_token(99999, "ghost@test.com", "gestion")
    monkeypatch.setattr(
        "controllers.auth_controller.load_token_from_file",
        lambda: token
    )
    deleted = {"called": False}

    def fake_delete():
        deleted["called"] = True

    monkeypatch.setattr("controllers.auth_controller.delete_token_file", fake_delete)

    ctrl = AuthController(db_session)
    assert ctrl.get_current_user() is None
    assert deleted["called"] is True


def test_token_file_save_load_delete_cycle(tmp_path):
    """Le cycle save/load/delete fonctionne sur un fichier explicite."""
    token_file = tmp_path / "token.txt"
    save_token_to_file("abc123", filepath=str(token_file))
    assert load_token_from_file(filepath=str(token_file)) == "abc123"
    delete_token_file(filepath=str(token_file))
    assert load_token_from_file(filepath=str(token_file)) is None
