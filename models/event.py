from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(200), nullable=False)
    event_date_start = Column(DateTime, nullable=False)
    event_date_end = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=False)
    attendees = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=False,
        unique=True)
    support_contact_id = Column(
        Integer, ForeignKey("employees.id"), nullable=True)

    contract = relationship("Contract", back_populates="event")
    support_contact = relationship("Employee", back_populates="events")

    def __repr__(self):
        date_str = self.event_date_start.strftime('%Y-%m-%d')
        return f"<Event {self.event_name} - {date_str}>"
