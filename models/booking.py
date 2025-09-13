from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum, DateTime, String
from enum import Enum
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class BookingStatus(str, Enum):
    reserved = "reserved"
    confirmed = "confirmed"
    cancelled = "cancelled"
    expired = "expired"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.reserved, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)  # When the reservation expires
    
    # Relationships
    user = relationship("User", backref="bookings")
    ticket = relationship("Ticket", backref="bookings")
