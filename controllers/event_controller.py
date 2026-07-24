from sqlalchemy.orm import Session
from models import Event, Contract, Employee
from utils import Permission, check_permission, log_exception
from typing import List, Optional
from datetime import datetime


class EventController:

    def __init__(self, db: Session):
        """Initialise le contrôleur des événements."""
        self.db = db

    def _require(self, current_user: dict, permission: str, message: str):
        """Valide une permission et lève une erreur si refusée."""
        if not check_permission(current_user.get('department'), permission):
            raise PermissionError(message)

    def _get_event(self, event_id: int) -> Optional[Event]:
        """Récupère un événement par identifiant."""
        return self.db.query(Event).filter(Event.id == event_id).first()

    def _get_contract(self, contract_id: int) -> Optional[Contract]:
        """Récupère un contrat par identifiant."""
        return self.db.query(Contract).filter(Contract.id == contract_id).first()

    def _get_employee(self, employee_id: int) -> Optional[Employee]:
        """Récupère un employé par identifiant."""
        return self.db.query(Employee).filter(Employee.id == employee_id).first()

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
        """Crée un nouvel événement lié à un contrat signé."""
        try:
            self._require(
                current_user,
                Permission.CREATE_EVENT,
                "Permission refusée pour créer un événement",
            )

            contract = self._get_contract(contract_id)
            if not contract:
                raise ValueError(f"Contrat {contract_id} non trouvé")

            if not contract.is_signed:
                raise ValueError(
                    "Le contrat doit être signé avant de créer "
                    "un événement")

            employee_id = current_user.get('employee_id')
            if contract.commercial_contact_id != employee_id:
                raise PermissionError(
                    "Vous ne pouvez créer un événement que pour "
                    "vos propres clients")

            existing = self.db.query(Event).filter(
                Event.contract_id == contract_id).first()
            if existing:
                raise ValueError(
                    "Un événement existe déjà pour le contrat "
                    f"{contract.contract_number}")

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
        """Liste les événements visibles par l'utilisateur courant."""
        try:
            dept = current_user.get('department')
            if not check_permission(dept, Permission.READ_ALL_EVENTS):
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
        """Récupère un événement par identifiant selon les droits."""
        try:
            event = self._get_event(event_id)
            if not event:
                return None

            dept = current_user.get('department')
            if check_permission(dept, Permission.READ_ALL_EVENTS):
                return event

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
        """Liste les événements assignés au support courant."""
        try:
            employee_id = current_user.get('employee_id')
            return self.db.query(Event).filter(
                Event.support_contact_id == employee_id
            ).all()

        except Exception as e:
            log_exception(e, {"action": "get_my_events"})
            raise

    def get_events_without_support(self, current_user: dict) -> List[Event]:
        """Liste les événements sans support assigné."""
        try:
            self._require(
                current_user,
                Permission.READ_ALL_EVENTS,
                "Permission refusée",
            )
            return self.db.query(Event).filter(Event.support_contact_id.is_(None)).all()

        except Exception as e:
            log_exception(e, {"action": "get_events_without_support"})
            raise

    def update_event(
        self,
        current_user: dict,
        event_id: int,
        **kwargs
    ) -> Event:
        """Met à jour un événement assigné au support courant."""
        try:
            self._require(
                current_user,
                Permission.UPDATE_OWN_EVENTS,
                "Permission refusée pour modifier un événement",
            )

            event = self._get_event(event_id)
            if not event:
                raise ValueError(f"Événement {event_id} non trouvé")

            employee_id = current_user.get('employee_id')
            if event.support_contact_id != employee_id:
                raise PermissionError(
                    "Vous ne pouvez modifier que vos propres événements")

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
        """Assigne un membre du support à un événement."""
        try:
            self._require(
                current_user,
                Permission.ASSIGN_SUPPORT,
                "Permission refusée pour assigner un support",
            )

            event = self._get_event(event_id)
            if not event:
                raise ValueError(f"Événement {event_id} non trouvé")

            support = self._get_employee(support_id)
            if not support:
                raise ValueError(f"Employé {support_id} non trouvé")

            if not support.is_support:
                raise ValueError(
                    f"L'employé {support.full_name} n'est pas du "
                    "département support")

            event.support_contact_id = support_id

            self.db.commit()
            self.db.refresh(event)

            return event

        except Exception as e:
            self.db.rollback()
            log_exception(
                e, {"action": "assign_support", "event_id": event_id})
            raise
