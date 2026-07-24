from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from config import Base


class Department(enum.Enum):
    COMMERCIAL = "commercial"
    SUPPORT = "support"
    GESTION = "gestion"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(
        String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    department = Column(
        SQLEnum(Department, native_enum=False), nullable=False)

    clients = relationship(
        "Client",
        back_populates="commercial_contact",
        foreign_keys="Client.commercial_contact_id")
    contracts = relationship("Contract", back_populates="commercial_contact")
    events = relationship("Event", back_populates="support_contact")

    def __repr__(self):
        return (
            f"<Employee {self.employee_number}: {self.full_name} "
            f"({self.department.value})>"
        )

    @property
    def is_commercial(self):
        return self.department == Department.COMMERCIAL

    @property
    def is_support(self):
        return self.department == Department.SUPPORT

    @property
    def is_gestion(self):
        return self.department == Department.GESTION
