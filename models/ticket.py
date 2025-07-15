from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum, String, Numeric
from enum import Enum
from sqlalchemy.orm import relationship
from core.database import Base

class TicketStatus(str, Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)
    user_id = Column(Integer, nullable=True)  # Nullable if not booked
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.available, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    seat = Column(String, nullable=True)

    show = relationship("Show", back_populates="tickets")