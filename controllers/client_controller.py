"""
Controller pour la gestion des clients
"""
from sqlalchemy.orm import Session
from models.client import Client
from utils.permissions import Permission, check_permission
from utils.sentry_logger import log_exception
from typing import List, Optional
from datetime import datetime


class ClientController:
    """Contrôleur pour gérer les opérations CRUD sur les clients"""

    def __init__(self, db: Session):
        self.db = db

    def create_client(
        self,
        current_user: dict,
        full_name: str,
        email: str,
        phone: str,
        company_name: str
    ) -> Client:
        """
        Crée un nouveau client

        Args:
            current_user: L'utilisateur authentifié
            full_name: Nom complet
            email: Email
            phone: Téléphone
            company_name: Nom de l'entreprise

        Returns:
            Le client créé
        """
        try:
            # Vérifier les permissions
            dept = current_user.get('department')
            if not check_permission(dept, Permission.CREATE_CLIENT):
                raise PermissionError(
                    "Permission refusée pour créer un client")

            # Vérifier que l'email n'existe pas
            existing = self.db.query(Client).filter(
                Client.email == email).first()
            if existing:
                raise ValueError(
                    f"Un client avec l'email {email} existe déjà")

            # Créer le client
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
        """
        Récupère tous les clients

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des clients
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_CLIENTS):
                raise PermissionError(
                    "Permission refusée pour lire les clients")

            return self.db.query(Client).all()

        except Exception as e:
            log_exception(e, {"action": "get_all_clients"})
            raise

    def get_client_by_id(
        self, current_user: dict, client_id: int
    ) -> Optional[Client]:
        """
        Récupère un client par son ID

        Args:
            current_user: L'utilisateur authentifié
            client_id: ID du client

        Returns:
            Le client ou None
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_CLIENTS):
                # Vérifier si c'est son propre client
                if check_permission(dept, Permission.READ_OWN_CLIENTS):
                    employee_id = current_user.get('employee_id')
                    return self.db.query(Client).filter(
                        Client.id == client_id,
                        Client.commercial_contact_id == employee_id,
                    ).first()
                raise PermissionError(
                    "Permission refusée pour lire ce client")

            return self.db.query(Client).filter(
                Client.id == client_id).first()

        except Exception as e:
            log_exception(
                e, {"action": "get_client_by_id", "client_id": client_id})
            raise

    def get_my_clients(self, current_user: dict) -> List[Client]:
        """
        Récupère les clients d'un commercial

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des clients
        """
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
        """
        Met à jour un client

        Args:
            current_user: L'utilisateur authentifié
            client_id: ID du client
            **kwargs: Champs à mettre à jour

        Returns:
            Le client modifié
        """
        try:
            # Récupérer le client
            client = self.db.query(Client).filter(
                Client.id == client_id).first()
            if not client:
                raise ValueError(f"Client {client_id} non trouvé")

            # Vérifier les permissions
            dept = current_user.get('department')
            if not check_permission(dept, Permission.UPDATE_OWN_CLIENTS):
                raise PermissionError(
                    "Permission refusée pour modifier un client")

            # Vérifier que c'est son propre client
            employee_id = current_user.get('employee_id')
            if client.commercial_contact_id != employee_id:
                raise PermissionError(
                    "Vous ne pouvez modifier que vos propres clients")

            # Mettre à jour les champs
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
