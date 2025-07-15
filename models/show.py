from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from core.database import Base

class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    performer = Column(String, nullable=True)

    tickets = relationship("Ticket", back_populates="show")