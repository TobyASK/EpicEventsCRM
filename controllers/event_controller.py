"""
Controller pour la gestion des événements
"""
from sqlalchemy.orm import Session
from models.event import Event
from models.contract import Contract
from models.employee import Employee
from utils.permissions import Permission, check_permission
from utils.sentry_logger import log_exception
from typing import List, Optional
from datetime import datetime


class EventController:
    """Contrôleur pour gérer les opérations CRUD sur les événements"""

    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        current_user: dict,
        contract_id: int,
        event_name: str,
        event_date_start: datetime,
        event_date_end: datetime,
        location: str,
        attendees: int,
        notes: str = None
    ) -> Event:
        """
        Crée un nouvel événement

        Args:
            current_user: L'utilisateur authentifié
            contract_id: ID du contrat
            event_name: Nom de l'événement
            event_date_start: Date de début
            event_date_end: Date de fin
            location: Lieu
            attendees: Nombre de participants
            notes: Notes

        Returns:
            L'événement créé
        """
        try:
            # Vérifier les permissions
            dept = current_user.get('department')
            if not check_permission(dept, Permission.CREATE_EVENT):
                raise PermissionError(
                    "Permission refusée pour créer un événement")

            # Vérifier que le contrat existe et est signé
            contract = self.db.query(Contract).filter(
                Contract.id == contract_id).first()
            if not contract:
                raise ValueError(f"Contrat {contract_id} non trouvé")

            if not contract.is_signed:
                raise ValueError(
                    "Le contrat doit être signé avant de créer "
                    "un événement")

            # Le commercial ne peut créer un événement que pour
            # ses propres clients
            employee_id = current_user.get('employee_id')
            if contract.commercial_contact_id != employee_id:
                raise PermissionError(
                    "Vous ne pouvez créer un événement que pour "
                    "vos propres clients")

            # Vérifier qu'il n'y a pas déjà un événement pour ce contrat
            existing = self.db.query(Event).filter(
                Event.contract_id == contract_id).first()
            if existing:
                raise ValueError(
                    "Un événement existe déjà pour le contrat "
                    f"{contract.contract_number}")

            # Créer l'événement
            event = Event(
                contract_id=contract_id,
                event_name=event_name,
                event_date_start=event_date_start,
                event_date_end=event_date_end,
                location=location,
                attendees=attendees,
                notes=notes
            )

            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            return event

        except Exception as e:
            self.db.rollback()
            log_exception(
                e, {"action": "create_event", "contract_id": contract_id})
            raise

    def get_all_events(self, current_user: dict) -> List[Event]:
        """
        Récupère tous les événements

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des événements
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_EVENTS):
                # Si c'est un support, ne récupérer que ses propres
                # événements
                if check_permission(dept, Permission.READ_OWN_EVENTS):
                    return self.get_my_events(current_user)
                raise PermissionError(
                    "Permission refusée pour lire les événements")

            return self.db.query(Event).all()

        except Exception as e:
            log_exception(e, {"action": "get_all_events"})
            raise

    def get_event_by_id(
        self, current_user: dict, event_id: int
    ) -> Optional[Event]:
        """
        Récupère un événement par son ID

        Args:
            current_user: L'utilisateur authentifié
            event_id: ID de l'événement

        Returns:
            L'événement ou None
        """
        try:
            event = self.db.query(Event).filter(
                Event.id == event_id).first()
            if not event:
                return None

            # Vérifier les permissions
            dept = current_user.get('department')
            if check_permission(dept, Permission.READ_ALL_EVENTS):
                return event

            # Si support, vérifier que c'est son événement
            if check_permission(dept, Permission.READ_OWN_EVENTS):
                employee_id = current_user.get('employee_id')
                if event.support_contact_id == employee_id:
                    return event

            raise PermissionError(
                "Permission refusée pour lire cet événement")

        except Exception as e:
            log_exception(
                e, {"action": "get_event_by_id", "event_id": event_id})
            raise

    def get_my_events(self, current_user: dict) -> List[Event]:
        """
        Récupère les événements d'un membre du support

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des événements
        """
        try:
            employee_id = current_user.get('employee_id')
            return self.db.query(Event).filter(
                Event.support_contact_id == employee_id
            ).all()

        except Exception as e:
            log_exception(e, {"action": "get_my_events"})
            raise

    def get_events_without_support(self, current_user: dict) -> List[Event]:
        """
        Récupère les événements sans contact support assigné

        Args:
            current_user: L'utilisateur authentifié

        Returns:
            Liste des événements sans support
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_EVENTS):
                raise PermissionError("Permission refusée")

            # == None (et non `is None`) est requis par SQLAlchemy
            # pour générer le SQL
            return self.db.query(Event).filter(
                Event.support_contact_id == None  # noqa: E711
            ).all()

        except Exception as e:
            log_exception(e, {"action": "get_events_without_support"})
            raise

    def update_event(
        self,
        current_user: dict,
        event_id: int,
        **kwargs
    ) -> Event:
        """
        Met à jour un événement

        Args:
            current_user: L'utilisateur authentifié
            event_id: ID de l'événement
            **kwargs: Champs à mettre à jour

        Returns:
            L'événement modifié
        """
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.UPDATE_OWN_EVENTS):
                raise PermissionError(
                    "Permission refusée pour modifier un événement")

            event = self.db.query(Event).filter(
                Event.id == event_id).first()
            if not event:
                raise ValueError(f"Événement {event_id} non trouvé")

            employee_id = current_user.get('employee_id')
            if event.support_contact_id != employee_id:
                raise PermissionError(
                    "Vous ne pouvez modifier que vos propres événements")

            # Mettre à jour les champs
            if 'event_name' in kwargs:
                event.event_name = kwargs['event_name']
            if 'event_date_start' in kwargs:
                event.event_date_start = kwargs['event_date_start']
            if 'event_date_end' in kwargs:
                event.event_date_end = kwargs['event_date_end']
            if 'location' in kwargs:
                event.location = kwargs['location']
            if 'attendees' in kwargs:
                event.attendees = kwargs['attendees']
            if 'notes' in kwargs:
                event.notes = kwargs['notes']

            self.db.commit()
            self.db.refresh(event)

            return event

        except Exception as e:
            self.db.rollback()
            log_exception(
                e, {"action": "update_event", "event_id": event_id})
            raise

    def assign_support(
        self,
        current_user: dict,
        event_id: int,
        support_id: int
    ) -> Event:
        """
        Assigne un membre du support à un événement

        Args:
            current_user: L'utilisateur authentifié
            event_id: ID de l'événement
            support_id: ID du membre du support

        Returns:
            L'événement modifié
        """
        try:
            # Vérifier les permissions
            dept = current_user.get('department')
            if not check_permission(dept, Permission.ASSIGN_SUPPORT):
                raise PermissionError(
                    "Permission refusée pour assigner un support")

            # Récupérer l'événement
            event = self.db.query(Event).filter(
                Event.id == event_id).first()
            if not event:
                raise ValueError(f"Événement {event_id} non trouvé")

            # Vérifier que le support existe et est du département support
            support = self.db.query(Employee).filter(
                Employee.id == support_id).first()
            if not support:
                raise ValueError(f"Employé {support_id} non trouvé")

            if not support.is_support:
                raise ValueError(
                    f"L'employé {support.full_name} n'est pas du "
                    "département support")

            # Assigner le support
            event.support_contact_id = support_id

            self.db.commit()
            self.db.refresh(event)

            return event

        except Exception as e:
            self.db.rollback()
            log_exception(
                e, {"action": "assign_support", "event_id": event_id})
            raise
