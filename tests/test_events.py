"""
Tests unitaires et d'intégration — EventController.
"""
import pytest
from datetime import datetime
from controllers.client_controller import ClientController
from controllers.contract_controller import ContractController
from controllers.event_controller import EventController


# ── Helpers / fixtures locales ──────────────────────────────────────────

START = datetime(2026, 9, 1, 14, 0)
END = datetime(2026, 9, 1, 18, 0)


@pytest.fixture
def setup(db_session, admin_user, commercial_user):
    """
    Retourne un contrat signé appartenant au commercial_user,
    prêt à servir de base pour les tests d'événements.
    """
    # Client du commercial
    client = ClientController(db_session).create_client(
        commercial_user, "Evt Client", "evt@test.com", "+1", "Evt Co"
    )
    # Contrat créé par gestion, contact commercial = commercial_user
    cc = ContractController(db_session)
    contract = cc.create_contract(
        admin_user, "CT-EVT", client.id, 5000.0)
    contract.commercial_contact_id = commercial_user["employee_id"]
    db_session.commit()
    signed = cc.sign_contract(admin_user, contract.id)
    return {"client": client, "contract": signed}


@pytest.fixture
def other_commercial(db_session):
    """Second commercial indépendant."""
    from models.employee import Employee, Department
    from utils.auth import hash_password
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


# ── Tests création ──────────────────────────────────────────────────────

def test_create_event(db_session, commercial_user, setup):
    """Un commercial peut créer un événement sur son contrat signé."""
    ctrl = EventController(db_session)
    evt = ctrl.create_event(
        commercial_user, setup["contract"].id, "Launch Party",
        START, END, "Paris", 100,
    )
    assert evt.id is not None
    assert evt.event_name == "Launch Party"
    assert evt.support_contact_id is None


def test_create_event_unsigned_contract(
    db_session, admin_user, commercial_user, setup
):
    """Créer un événement sur un contrat non signé lève ValueError."""
    cc = ContractController(db_session)
    unsigned = cc.create_contract(
        admin_user, "CT-UNSIG", setup["client"].id, 1000.0)
    unsigned.commercial_contact_id = commercial_user["employee_id"]
    db_session.commit()
    with pytest.raises(ValueError, match="signé"):
        EventController(db_session).create_event(
            commercial_user, unsigned.id, "Nope", START, END, "X", 10
        )


def test_create_event_wrong_commercial(
    db_session, other_commercial, setup
):
    """Un commercial ne peut pas créer d'événement pour un autre."""
    with pytest.raises(PermissionError, match="propres clients"):
        EventController(db_session).create_event(
            other_commercial, setup["contract"].id, "Stolen",
            START, END, "Y", 5
        )


def test_create_event_duplicate_contract(
    db_session, commercial_user, setup
):
    """Un contrat ne peut avoir qu'un seul événement."""
    ctrl = EventController(db_session)
    ctrl.create_event(
        commercial_user, setup["contract"].id, "First",
        START, END, "A", 10)
    with pytest.raises(ValueError, match="existe déjà"):
        ctrl.create_event(
            commercial_user, setup["contract"].id, "Second",
            START, END, "B", 10)


def test_admin_cannot_create_event(db_session, admin_user, setup):
    """Gestion n'a pas la permission de créer un événement."""
    with pytest.raises(PermissionError):
        EventController(db_session).create_event(
            admin_user, setup["contract"].id, "X", START, END, "X", 1
        )


# ── Tests lecture ───────────────────────────────────────────────────────

def test_get_all_events(db_session, commercial_user, setup):
    """get_all_events retourne tous les événements."""
    ctrl = EventController(db_session)
    ctrl.create_event(
        commercial_user, setup["contract"].id, "E1",
        START, END, "P", 50)
    assert len(ctrl.get_all_events(commercial_user)) == 1


def test_get_my_events(db_session, commercial_user, support_user, setup):
    """get_my_events ne retourne que les événements du support."""
    ec = EventController(db_session)
    evt = ec.create_event(
        commercial_user, setup["contract"].id, "E",
        START, END, "P", 10)
    # Assigner support
    ec.assign_support(
        {"employee_id": 0, "email": "x", "department": "gestion"},
        evt.id, support_user["employee_id"]
    )
    mine = ec.get_my_events(support_user)
    assert len(mine) == 1
    assert mine[0].id == evt.id


def test_get_events_without_support(
    db_session, admin_user, commercial_user, setup
):
    """get_events_without_support ne retourne que les non assignés."""
    ctrl = EventController(db_session)
    evt = ctrl.create_event(
        commercial_user, setup["contract"].id, "NoSupport",
        START, END, "P", 10)
    results = ctrl.get_events_without_support(admin_user)
    assert any(e.id == evt.id for e in results)


# ── Tests mise à jour ───────────────────────────────────────────────────

def test_support_can_update_own_event(
    db_session, admin_user, commercial_user, support_user, setup
):
    """Un support peut modifier l'événement qui lui est assigné."""
    ec = EventController(db_session)
    evt = ec.create_event(
        commercial_user, setup["contract"].id, "Before",
        START, END, "OldPlace", 10)
    ec.assign_support(
        {"employee_id": 0, "email": "x", "department": "gestion"},
        evt.id, support_user["employee_id"]
    )
    updated = ec.update_event(
        support_user, evt.id, event_name="After", location="NewPlace")
    assert updated.event_name == "After"
    assert updated.location == "NewPlace"


def test_support_cannot_update_unassigned_event(
    db_session, commercial_user, support_user, setup
):
    """Un support ne peut pas modifier un événement non assigné."""
    ec = EventController(db_session)
    evt = ec.create_event(
        commercial_user, setup["contract"].id, "NotMine",
        START, END, "P", 5)
    with pytest.raises(PermissionError, match="propres événements"):
        ec.update_event(support_user, evt.id, event_name="Stolen")


def test_commercial_cannot_update_event(
    db_session, commercial_user, setup
):
    """Un commercial n'a pas la permission de modifier un événement."""
    ec = EventController(db_session)
    evt = ec.create_event(
        commercial_user, setup["contract"].id, "CannotEdit",
        START, END, "P", 5)
    with pytest.raises(PermissionError):
        ec.update_event(commercial_user, evt.id, event_name="X")


# ── Tests assignation support ───────────────────────────────────────────

def test_assign_support(
    db_session, admin_user, commercial_user, support_user, setup
):
    """Gestion peut assigner un support à un événement."""
    ec = EventController(db_session)
    evt = ec.create_event(
        commercial_user, setup["contract"].id, "Assign Test",
        START, END, "P", 20)
    updated = ec.assign_support(
        admin_user, evt.id, support_user["employee_id"])
    assert updated.support_contact_id == support_user["employee_id"]


def test_assign_non_support_employee(
    db_session, admin_user, commercial_user, setup
):
    """Assigner un employé hors département support lève ValueError."""
    ec = EventController(db_session)
    evt = ec.create_event(
        commercial_user, setup["contract"].id, "Assign Fail",
        START, END, "P", 20)
    with pytest.raises(ValueError, match="département support"):
        ec.assign_support(
            admin_user, evt.id, commercial_user["employee_id"])


def test_commercial_cannot_assign_support(
    db_session, commercial_user, support_user, setup
):
    """Un commercial n'a pas la permission d'assigner un support."""
    ec = EventController(db_session)
    evt = ec.create_event(
        commercial_user, setup["contract"].id, "No Assign",
        START, END, "P", 10)
    with pytest.raises(PermissionError):
        ec.assign_support(
            commercial_user, evt.id, support_user["employee_id"])
