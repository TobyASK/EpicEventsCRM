import pytest
from controllers.client_controller import ClientController


@pytest.fixture
def other_commercial(db_session):
    from models import Employee, Department
    from utils import hash_password
    emp = Employee(
        employee_number="COM002",
        full_name="Other Commercial",
        email="other@test.com",
        password_hash=hash_password("pass"),
        department=Department.COMMERCIAL,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return {
        "employee_id": emp.id,
        "email": emp.email,
        "department": emp.department.value,
    }


def test_create_client(db_session, commercial_user):
    ctrl = ClientController(db_session)
    client = ctrl.create_client(
        commercial_user,
        "Kevin Casey",
        "kevin@test.com",
        "+33600000000",
        "Startup LLC")
    assert client.id is not None
    assert client.commercial_contact_id == commercial_user["employee_id"]


def test_create_client_duplicate_email(db_session, commercial_user):
    ctrl = ClientController(db_session)
    ctrl.create_client(
        commercial_user, "Client A", "dup@test.com", "+1", "Co A")
    with pytest.raises(ValueError, match="existe déjà"):
        ctrl.create_client(
            commercial_user, "Client B", "dup@test.com", "+2", "Co B")


def test_admin_cannot_create_client(db_session, admin_user):
    ctrl = ClientController(db_session)
    with pytest.raises(PermissionError):
        ctrl.create_client(admin_user, "X", "x@x.com", "+0", "X")


def test_get_all_clients(db_session, commercial_user):
    ctrl = ClientController(db_session)
    ctrl.create_client(commercial_user, "A", "a@test.com", "+1", "Co A")
    ctrl.create_client(commercial_user, "B", "b@test.com", "+2", "Co B")
    assert len(ctrl.get_all_clients(commercial_user)) == 2


def test_get_my_clients(db_session, commercial_user, other_commercial):
    ctrl = ClientController(db_session)
    ctrl.create_client(
        commercial_user, "Mine", "mine@test.com", "+1", "Co")
    ctrl.create_client(
        other_commercial, "Other", "other@test.com", "+2", "Co")
    mine = ctrl.get_my_clients(commercial_user)
    assert len(mine) == 1
    assert mine[0].email == "mine@test.com"


def test_update_own_client(db_session, commercial_user):
    ctrl = ClientController(db_session)
    c = ctrl.create_client(
        commercial_user, "Original", "orig@test.com", "+1", "OldCo")
    updated = ctrl.update_client(
        commercial_user, c.id, full_name="Updated", company_name="NewCo")
    assert updated.full_name == "Updated"
    assert updated.company_name == "NewCo"
    assert updated.email == "orig@test.com"  # champ non modifié


def test_update_other_commercial_client_forbidden(
    db_session, commercial_user, other_commercial
):
    """Vérifie qu'un commercial ne peut pas modifier un client d'un autre."""
    ctrl = ClientController(db_session)
    c = ctrl.create_client(
        other_commercial, "Theirs", "theirs@test.com", "+1", "Co")
    with pytest.raises(PermissionError, match="propres clients"):
        ctrl.update_client(commercial_user, c.id, full_name="Stolen")


def test_support_cannot_update_client(
    db_session, support_user, commercial_user
):
    """Vérifie qu'un support ne peut pas modifier un client."""
    ctrl = ClientController(db_session)
    c = ctrl.create_client(
        commercial_user, "C", "c@test.com", "+1", "Co")
    with pytest.raises(PermissionError):
        ctrl.update_client(support_user, c.id, full_name="X")
