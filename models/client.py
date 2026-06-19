"""
Modèle Client - Représente un client d'Epic Events
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Client(Base):
    """
    Modèle Client
    Représente un client de l'entreprise
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    company_name = Column(String(100), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_contact_date = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False)

    # Clé étrangère vers le commercial responsable
    commercial_contact_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False)

    # Relations
    commercial_contact = relationship(
        "Employee",
        back_populates="clients",
        foreign_keys=[commercial_contact_id])
    contracts = relationship(
        "Contract", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.full_name} - {self.company_name}>"
