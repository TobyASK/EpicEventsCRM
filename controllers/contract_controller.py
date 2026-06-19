"""
Controller pour la gestion des contrats
"""
from sqlalchemy.orm import Session
from models.contract import Contract
from models.client import Client
from utils.permissions import Permission, check_permission
from utils.sentry_logger import log_exception, log_contract_signed
from typing import List, Optional


class ContractController:
    """Contrôleur pour gérer les opérations CRUD sur les contrats"""

    def __init__(self, db: Session):
        self.db = db

    def create_contract(
        self,
        current_user: dict,
        contract_number: str,
        client_id: int,
        total_amount: float,
        amount_remaining: float = None
    ) -> Contract:
        """
        Crée un nouveau contrat

        Args:
            current_user: L'utilisateur authentifié
            contract_number: Numéro de contrat
            client_id: ID du client
            total_amount: Montant total
            amount_remaining: Montant restant (par défaut = montant total)

        Returns:
            Le contrat créé
        """
        try:
            # Vérifier les permissions
            dept = current_user.get('department')
            if not check_permission(dept, Permission.CREATE_CONTRACT):
                raise PermissionError(
                    "Permission refusée pour créer un contrat")

            # Vérifier que le contrat n'existe pas
            existing = self.db.query(Contract).filter(
                Contract.contract_number == contract_number).first()
            if existing:
                raise ValueError(
                    f"Le contrat {contract_number} existe déjà")

            # Vérifier que le client existe
            client = self.db.query(Client).filter(
                Client.id == client_id).first()
            if not client:
                raise ValueError(f"Client {client_id} non trouvé")

            # Par défaut, le montant restant = montant total
            if amount_remaining is None:
                amount_remaining = total_amount

            # Le contact commercial du contrat = l'utilisateur courant
            commercial_contact_id = current_user.get('employee_id')

            # Créer le contrat
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
        """
        Récupère tous les contrats

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des contrats
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_CONTRACTS):
                raise PermissionError(
                    "Permission refusée pour lire les contrats")

            return self.db.query(Contract).all()

        except Exception as e:
            log_exception(e, {"action": "get_all_contracts"})
            raise

    def get_contract_by_id(
        self, current_user: dict, contract_id: int
    ) -> Optional[Contract]:
        """
        Récupère un contrat par son ID

        Args:
            current_user: L'utilisateur authentifié
            contract_id: ID du contrat

        Returns:
            Le contrat ou None
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_CONTRACTS):
                raise PermissionError(
                    "Permission refusée pour lire les contrats")

            return self.db.query(Contract).filter(
                Contract.id == contract_id).first()

        except Exception as e:
            log_exception(e, {
                "action": "get_contract_by_id",
                "contract_id": contract_id,
            })
            raise

    def get_unsigned_contracts(self, current_user: dict) -> List[Contract]:
        """
        Récupère les contrats non signés

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des contrats non signés
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_CONTRACTS):
                raise PermissionError(
                    "Permission refusée pour lire les contrats")

            # == False (et non `is False`) est requis par SQLAlchemy
            # pour générer le SQL
            return self.db.query(Contract).filter(
                Contract.is_signed == False  # noqa: E712
            ).all()

        except Exception as e:
            log_exception(e, {"action": "get_unsigned_contracts"})
            raise

    def get_unpaid_contracts(self, current_user: dict) -> List[Contract]:
        """
        Récupère les contrats non payés

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des contrats avec montant restant > 0
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_CONTRACTS):
                raise PermissionError(
                    "Permission refusée pour lire les contrats")

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
        """
        Met à jour un contrat.

        Gestion peut modifier tous les contrats.
        Commercial peut modifier uniquement les contrats dont il
        est le contact commercial.

        Args:
            current_user: L'utilisateur authentifié
            contract_id: ID du contrat à modifier
            **kwargs: Champs à mettre à jour (total_amount,
                amount_remaining)

        Returns:
            Le contrat modifié

        Raises:
            PermissionError: Si l'utilisateur n'a pas les permissions
                requises
            ValueError: Si le contrat n'existe pas
        """
        try:
            dept = current_user.get('department')
            can_all = check_permission(dept, Permission.UPDATE_CONTRACT)
            can_own = check_permission(
                dept, Permission.UPDATE_OWN_CONTRACTS)

            if not can_all and not can_own:
                raise PermissionError(
                    "Permission refusée pour modifier un contrat")

            contract = self.db.query(Contract).filter(
                Contract.id == contract_id).first()
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
        """
        Signe un contrat

        Args:
            current_user: L'utilisateur authentifié
            contract_id: ID du contrat

        Returns:
            Le contrat signé
        """
        try:
            # Vérifier les permissions
            dept = current_user.get('department')
            if not check_permission(dept, Permission.SIGN_CONTRACT):
                raise PermissionError(
                    "Permission refusée pour signer un contrat")

            # Récupérer le contrat
            contract = self.db.query(Contract).filter(
                Contract.id == contract_id).first()
            if not contract:
                raise ValueError(f"Contrat {contract_id} non trouvé")

            if contract.is_signed:
                raise ValueError(
                    f"Le contrat {contract.contract_number} "
                    "est déjà signé")

            # Signer le contrat
            contract.is_signed = True

            self.db.commit()
            self.db.refresh(contract)

            # Journaliser la signature
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
