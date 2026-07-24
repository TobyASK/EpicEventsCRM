from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base


class Client(Base):
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

    commercial_contact_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False)

    commercial_contact = relationship(
        "Employee",
        back_populates="clients",
        foreign_keys=[commercial_contact_id])
    contracts = relationship(
        "Contract", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.full_name} - {self.company_name}>"
