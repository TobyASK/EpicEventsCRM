"""
Tests unitaires et d'intégration — ContractController.
"""
import pytest
from controllers.client_controller import ClientController
from controllers.contract_controller import ContractController


# ── Fixtures locales ────────────────────────────────────────────────────

@pytest.fixture
def client_obj(db_session, commercial_user):
    """Client appartenant au commercial de test."""
    ctrl = ClientController(db_session)
    return ctrl.create_client(
        commercial_user, "Test Client", "client@test.com", "+1",
        "Test Co")


@pytest.fixture
def signed_contract(db_session, admin_user, commercial_user, client_obj):
    """Contrat signé prêt à accueillir un événement."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(
        admin_user, "CT-SIGNED", client_obj.id, 10000.0, 5000.0)
    return ctrl.sign_contract(admin_user, c.id)


@pytest.fixture
def other_commercial(db_session):
    """Second commercial sans lien avec les clients du premier."""
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

def test_create_contract(db_session, admin_user, client_obj):
    """Gestion peut créer un contrat."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(admin_user, "CT-001", client_obj.id, 50000.0)
    assert c.id is not None
    assert c.contract_number == "CT-001"
    assert c.total_amount == 50000.0
    assert c.amount_remaining == 50000.0  # défaut = total_amount
    assert c.is_signed is False


def test_create_contract_amount_remaining_default(
    db_session, admin_user, client_obj
):
    """Sans montant restant, il vaut par défaut le montant total."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(
        admin_user, "CT-DEF", client_obj.id, 12000.0, None)
    assert c.amount_remaining == 12000.0


def test_commercial_cannot_create_contract(
    db_session, commercial_user, client_obj
):
    """Un commercial ne peut pas créer un contrat."""
    ctrl = ContractController(db_session)
    with pytest.raises(PermissionError):
        ctrl.create_contract(
            commercial_user, "CT-X", client_obj.id, 1000.0)


def test_create_contract_duplicate_number(
    db_session, admin_user, client_obj
):
    """Un numéro de contrat en doublon lève ValueError."""
    ctrl = ContractController(db_session)
    ctrl.create_contract(admin_user, "CT-DUP", client_obj.id, 1000.0)
    with pytest.raises(ValueError, match="existe déjà"):
        ctrl.create_contract(admin_user, "CT-DUP", client_obj.id, 2000.0)


def test_create_contract_client_not_found(db_session, admin_user):
    """Créer un contrat pour un client inexistant lève ValueError."""
    ctrl = ContractController(db_session)
    with pytest.raises(ValueError, match="non trouvé"):
        ctrl.create_contract(admin_user, "CT-NF", 99999, 1000.0)


# ── Tests lecture ───────────────────────────────────────────────────────

def test_get_all_contracts(db_session, admin_user, client_obj):
    """Tous les collaborateurs peuvent lire la liste des contrats."""
    ctrl = ContractController(db_session)
    ctrl.create_contract(admin_user, "A", client_obj.id, 1000.0)
    ctrl.create_contract(admin_user, "B", client_obj.id, 2000.0)
    assert len(ctrl.get_all_contracts(admin_user)) == 2


def test_get_unsigned_contracts(db_session, admin_user, client_obj):
    """get_unsigned_contracts ne retourne que les contrats non signés."""
    ctrl = ContractController(db_session)
    c1 = ctrl.create_contract(admin_user, "CT-U1", client_obj.id, 1000.0)
    c2 = ctrl.create_contract(admin_user, "CT-U2", client_obj.id, 2000.0)
    ctrl.sign_contract(admin_user, c1.id)
    unsigned = ctrl.get_unsigned_contracts(admin_user)
    ids = [c.id for c in unsigned]
    assert c1.id not in ids
    assert c2.id in ids


def test_get_unpaid_contracts(db_session, admin_user, client_obj):
    """get_unpaid_contracts ne retourne que les contrats à solde > 0."""
    ctrl = ContractController(db_session)
    paid = ctrl.create_contract(
        admin_user, "CT-P", client_obj.id, 1000.0, 0.0)
    unpaid = ctrl.create_contract(
        admin_user, "CT-NP", client_obj.id, 1000.0, 500.0)
    results = ctrl.get_unpaid_contracts(admin_user)
    ids = [c.id for c in results]
    assert paid.id not in ids
    assert unpaid.id in ids


# ── Tests mise à jour ───────────────────────────────────────────────────

def test_gestion_can_update_any_contract(
    db_session, admin_user, client_obj
):
    """Gestion peut modifier n'importe quel contrat."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(admin_user, "CT-G", client_obj.id, 1000.0)
    updated = ctrl.update_contract(
        admin_user, c.id, total_amount=2000.0, amount_remaining=1500.0)
    assert updated.total_amount == 2000.0
    assert updated.amount_remaining == 1500.0


def test_commercial_can_update_own_contract(
    db_session, admin_user, commercial_user, client_obj
):
    """Un commercial peut modifier les contrats de ses clients."""
    ctrl = ContractController(db_session)
    # Le contrat est créé par la gestion ; on force ensuite le contact
    # commercial à commercial_user pour vérifier qu'il peut le modifier.
    c = ctrl.create_contract(admin_user, "CT-COM", client_obj.id, 1000.0)
    c.commercial_contact_id = commercial_user["employee_id"]
    db_session.commit()
    updated = ctrl.update_contract(
        commercial_user, c.id, amount_remaining=200.0)
    assert updated.amount_remaining == 200.0


def test_commercial_cannot_update_other_contract(
    db_session, admin_user, commercial_user, other_commercial, client_obj
):
    """Un commercial ne peut pas modifier le contrat d'un autre."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(admin_user, "CT-OTH", client_obj.id, 1000.0)
    # Contact commercial = other_commercial
    c.commercial_contact_id = other_commercial["employee_id"]
    db_session.commit()
    with pytest.raises(PermissionError, match="vos clients"):
        ctrl.update_contract(commercial_user, c.id, amount_remaining=0.0)


# ── Tests signature ─────────────────────────────────────────────────────

def test_sign_contract(db_session, admin_user, client_obj):
    """Gestion peut signer un contrat non signé."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(admin_user, "CT-S", client_obj.id, 5000.0)
    assert c.is_signed is False
    signed = ctrl.sign_contract(admin_user, c.id)
    assert signed.is_signed is True


def test_sign_already_signed_contract(db_session, admin_user, client_obj):
    """Signer un contrat déjà signé lève ValueError."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(admin_user, "CT-SS", client_obj.id, 5000.0)
    ctrl.sign_contract(admin_user, c.id)
    with pytest.raises(ValueError, match="déjà signé"):
        ctrl.sign_contract(admin_user, c.id)


def test_commercial_cannot_sign_contract(
    db_session, commercial_user, admin_user, client_obj
):
    """Un commercial ne peut pas signer un contrat."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(admin_user, "CT-CS", client_obj.id, 1000.0)
    with pytest.raises(PermissionError):
        ctrl.sign_contract(commercial_user, c.id)


# ── Tests is_fully_paid ─────────────────────────────────────────────────

def test_is_fully_paid_true(db_session, admin_user, client_obj):
    """is_fully_paid est True quand amount_remaining <= 0."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(
        admin_user, "CT-FP", client_obj.id, 1000.0, 0.0)
    assert c.is_fully_paid is True


def test_is_fully_paid_false(db_session, admin_user, client_obj):
    """is_fully_paid est False quand amount_remaining > 0."""
    ctrl = ContractController(db_session)
    c = ctrl.create_contract(
        admin_user, "CT-NP2", client_obj.id, 1000.0, 500.0)
    assert c.is_fully_paid is False
