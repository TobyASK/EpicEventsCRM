from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(
        String(50), unique=True, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    amount_remaining = Column(Float, nullable=False)
    is_signed = Column(Boolean, default=False, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    commercial_contact_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False)

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
        return self.amount_remaining <= 0
