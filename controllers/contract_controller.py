from sqlalchemy import false
from sqlalchemy.orm import Session
from models import Contract, Client, Employee, Department
from utils import (
    Permission,
    check_permission,
    log_exception,
    log_contract_signed,
)
from typing import List, Optional


class ContractController:

    def __init__(self, db: Session):
        """Initialise le contrôleur des contrats."""
        self.db = db

    def _require(self, current_user: dict, permission: str, message: str):
        """Valide une permission et lève une erreur si refusée."""
        if not check_permission(current_user.get('department'), permission):
            raise PermissionError(message)

    def _get_contract(self, contract_id: int) -> Optional[Contract]:
        """Récupère un contrat par son identifiant."""
        return self.db.query(Contract).filter(Contract.id == contract_id).first()

    def _get_client(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son identifiant."""
        return self.db.query(Client).filter(Client.id == client_id).first()

    def _get_employee(self, employee_id: int) -> Optional[Employee]:
        """Récupère un employé par son identifiant."""
        return self.db.query(Employee).filter(Employee.id == employee_id).first()

    def create_contract(
        self,
        current_user: dict,
        contract_number: str,
        client_id: int,
        total_amount: float,
        amount_remaining: float = None,
        commercial_contact_id: int = None,
    ) -> Contract:
        """Crée un nouveau contrat."""
        try:
            self._require(
                current_user,
                Permission.CREATE_CONTRACT,
                "Permission refusée pour créer un contrat",
            )

            existing = self.db.query(Contract).filter(
                Contract.contract_number == contract_number).first()
            if existing:
                raise ValueError(
                    f"Le contrat {contract_number} existe déjà")

            client = self._get_client(client_id)
            if not client:
                raise ValueError(f"Client {client_id} non trouvé")

            if amount_remaining is None:
                amount_remaining = total_amount

            if commercial_contact_id is None:
                commercial_contact_id = client.commercial_contact_id

            commercial_contact = self._get_employee(commercial_contact_id)
            if not commercial_contact:
                raise ValueError(
                    f"Employé commercial {commercial_contact_id} non trouvé")

            if commercial_contact.department != Department.COMMERCIAL:
                raise ValueError(
                    f"L'employé {commercial_contact.full_name} n'est pas commercial")

            contract = Contract(
                contract_number=contract_number,
                client_id=client_id,
                commercial_contact_id=commercial_contact_id,
                total_amount=total_amount,
                amount_remaining=amount_remaining,
                is_signed=False
            )

            self.db.add(contract)
            self.db.commit()
            self.db.refresh(contract)

            return contract

        except Exception as e:
            self.db.rollback()
            log_exception(e, {
                "action": "create_contract",
                "contract_number": contract_number,
            })
            raise

    def get_all_contracts(self, current_user: dict) -> List[Contract]:
        """Liste tous les contrats."""
        try:
            self._require(
                current_user,
                Permission.READ_ALL_CONTRACTS,
                "Permission refusée pour lire les contrats",
            )

            return self.db.query(Contract).all()

        except Exception as e:
            log_exception(e, {"action": "get_all_contracts"})
            raise

    def get_contract_by_id(
        self, current_user: dict, contract_id: int
    ) -> Optional[Contract]:
        """Récupère un contrat par son identifiant."""
        try:
            self._require(
                current_user,
                Permission.READ_ALL_CONTRACTS,
                "Permission refusée pour lire les contrats",
            )
            return self._get_contract(contract_id)

        except Exception as e:
            log_exception(e, {
                "action": "get_contract_by_id",
                "contract_id": contract_id,
            })
            raise

    def get_unsigned_contracts(self, current_user: dict) -> List[Contract]:
        """Liste les contrats non signés."""
        try:
            self._require(
                current_user,
                Permission.READ_ALL_CONTRACTS,
                "Permission refusée pour lire les contrats",
            )
            return self.db.query(Contract).filter(Contract.is_signed == false()).all()

        except Exception as e:
            log_exception(e, {"action": "get_unsigned_contracts"})
            raise

    def get_unpaid_contracts(self, current_user: dict) -> List[Contract]:
        """Liste les contrats ayant un reste à payer."""
        try:
            self._require(
                current_user,
                Permission.READ_ALL_CONTRACTS,
                "Permission refusée pour lire les contrats",
            )

            return self.db.query(Contract).filter(
                Contract.amount_remaining > 0).all()

        except Exception as e:
            log_exception(e, {"action": "get_unpaid_contracts"})
            raise

    def update_contract(
        self,
        current_user: dict,
        contract_id: int,
        **kwargs
    ) -> Contract:
        """Met à jour un contrat existant."""
        try:
            dept = current_user.get('department')
            can_all = check_permission(dept, Permission.UPDATE_CONTRACT)
            can_own = check_permission(
                dept, Permission.UPDATE_OWN_CONTRACTS)

            if not can_all and not can_own:
                raise PermissionError(
                    "Permission refusée pour modifier un contrat")

            contract = self._get_contract(contract_id)
            if not contract:
                raise ValueError(f"Contrat {contract_id} non trouvé")

            if can_own and not can_all:
                employee_id = current_user.get('employee_id')
                if contract.commercial_contact_id != employee_id:
                    raise PermissionError(
                        "Vous ne pouvez modifier que les contrats "
                        "de vos clients")

            if 'total_amount' in kwargs:
                contract.total_amount = kwargs['total_amount']
            if 'amount_remaining' in kwargs:
                contract.amount_remaining = kwargs['amount_remaining']

            self.db.commit()
            self.db.refresh(contract)

            return contract

        except Exception as e:
            self.db.rollback()
            log_exception(e, {
                "action": "update_contract",
                "contract_id": contract_id,
            })
            raise

    def sign_contract(
        self, current_user: dict, contract_id: int
    ) -> Contract:
        """Signe un contrat non encore signé."""
        try:
            self._require(
                current_user,
                Permission.SIGN_CONTRACT,
                "Permission refusée pour signer un contrat",
            )

            contract = self._get_contract(contract_id)
            if not contract:
                raise ValueError(f"Contrat {contract_id} non trouvé")

            if contract.is_signed:
                raise ValueError(
                    f"Le contrat {contract.contract_number} "
                    "est déjà signé")

            contract.is_signed = True

            self.db.commit()
            self.db.refresh(contract)

            log_contract_signed(
                contract.contract_number, contract.client.full_name)

            return contract

        except Exception as e:
            self.db.rollback()
            log_exception(e, {
                "action": "sign_contract",
                "contract_id": contract_id,
            })
            raise
