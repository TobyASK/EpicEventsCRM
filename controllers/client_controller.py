from sqlalchemy.orm import Session
from models import Client
from utils import Permission, check_permission, log_exception
from typing import List, Optional
from datetime import datetime


class ClientController:

    def __init__(self, db: Session):
        """Initialise le contrôleur des clients."""
        self.db = db

    def _require(self, current_user: dict, permission: str, message: str):
        """Valide une permission et lève une erreur si refusée."""
        if not check_permission(current_user.get('department'), permission):
            raise PermissionError(message)

    def _get_client(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son identifiant."""
        return self.db.query(Client).filter(Client.id == client_id).first()

    def create_client(
        self,
        current_user: dict,
        full_name: str,
        email: str,
        phone: str,
        company_name: str
    ) -> Client:
        """Crée un nouveau client."""
        try:
            self._require(
                current_user,
                Permission.CREATE_CLIENT,
                "Permission refusée pour créer un client",
            )

            existing = self.db.query(Client).filter(
                Client.email == email).first()
            if existing:
                raise ValueError(
                    f"Un client avec l'email {email} existe déjà")

            client = Client(
                full_name=full_name,
                email=email,
                phone=phone,
                company_name=company_name,
                commercial_contact_id=current_user.get('employee_id')
            )

            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)

            return client

        except Exception as e:
            self.db.rollback()
            log_exception(e, {"action": "create_client", "email": email})
            raise

    def get_all_clients(self, current_user: dict) -> List[Client]:
        """Liste tous les clients."""
        try:
            self._require(
                current_user,
                Permission.READ_ALL_CLIENTS,
                "Permission refusée pour lire les clients",
            )

            return self.db.query(Client).all()

        except Exception as e:
            log_exception(e, {"action": "get_all_clients"})
            raise

    def get_client_by_id(
        self, current_user: dict, client_id: int
    ) -> Optional[Client]:
        """Récupère un client par ID selon les droits du profil."""
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_CLIENTS):
                if check_permission(dept, Permission.READ_OWN_CLIENTS):
                    employee_id = current_user.get('employee_id')
                    return self.db.query(Client).filter(
                        Client.id == client_id,
                        Client.commercial_contact_id == employee_id,
                    ).first()
                raise PermissionError(
                    "Permission refusée pour lire ce client")

            return self._get_client(client_id)

        except Exception as e:
            log_exception(
                e, {"action": "get_client_by_id", "client_id": client_id})
            raise

    def get_my_clients(self, current_user: dict) -> List[Client]:
        """Liste les clients rattachés au commercial courant."""
        try:
            employee_id = current_user.get('employee_id')
            return self.db.query(Client).filter(
                Client.commercial_contact_id == employee_id
            ).all()

        except Exception as e:
            log_exception(e, {"action": "get_my_clients"})
            raise

    def update_client(
        self,
        current_user: dict,
        client_id: int,
        **kwargs
    ) -> Client:
        """Met à jour un client appartenant au commercial courant."""
        try:
            client = self._get_client(client_id)
            if not client:
                raise ValueError(f"Client {client_id} non trouvé")

            self._require(
                current_user,
                Permission.UPDATE_OWN_CLIENTS,
                "Permission refusée pour modifier un client",
            )

            employee_id = current_user.get('employee_id')
            if client.commercial_contact_id != employee_id:
                raise PermissionError(
                    "Vous ne pouvez modifier que vos propres clients")

            if 'full_name' in kwargs:
                client.full_name = kwargs['full_name']
            if 'email' in kwargs:
                client.email = kwargs['email']
            if 'phone' in kwargs:
                client.phone = kwargs['phone']
            if 'company_name' in kwargs:
                client.company_name = kwargs['company_name']

            from datetime import timezone
            client.last_contact_date = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(client)

            return client

        except Exception as e:
            self.db.rollback()
            log_exception(
                e, {"action": "update_client", "client_id": client_id})
            raise
