"""
Modèle Contract - Représente un contrat entre Epic Events et un client
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Contract(Base):
    """
    Modèle Contract
    Représente un contrat signé avec un client
    """
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(
        String(50), unique=True, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    amount_remaining = Column(Float, nullable=False)
    is_signed = Column(Boolean, default=False, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Clés étrangères
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    commercial_contact_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False)

    # Relations
    client = relationship("Client", back_populates="contracts")
    commercial_contact = relationship(
        "Employee", back_populates="contracts")
    event = relationship(
        "Event",
        back_populates="contract",
        uselist=False,
        cascade="all, delete-orphan")

    def __repr__(self):
        status = "Signé" if self.is_signed else "Non signé"
        return (
            f"<Contract {self.contract_number} - {status} - "
            f"{self.total_amount}€>"
        )

    @property
    def is_fully_paid(self):
        """True si le montant restant est nul ou négatif
        (contrat entièrement payé)."""
        return self.amount_remaining <= 0
