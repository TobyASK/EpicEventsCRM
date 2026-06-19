"""
Modèle Event - Représente un événement organisé pour un client
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Event(Base):
    """
    Modèle Event
    Représente un événement organisé dans le cadre d'un contrat
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(200), nullable=False)
    event_date_start = Column(DateTime, nullable=False)
    event_date_end = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=False)
    attendees = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Clés étrangères
    contract_id = Column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=False,
        unique=True)
    support_contact_id = Column(
        Integer, ForeignKey("employees.id"), nullable=True)

    # Relations
    contract = relationship("Contract", back_populates="event")
    support_contact = relationship("Employee", back_populates="events")

    def __repr__(self):
        date_str = self.event_date_start.strftime('%Y-%m-%d')
        return f"<Event {self.event_name} - {date_str}>"
