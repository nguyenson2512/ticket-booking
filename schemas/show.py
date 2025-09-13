from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from schemas.ticket import TicketOut


class TicketClassInput(BaseModel):
    ticket_class: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)


class ShowCreate(BaseModel):
    name: str
    location: str
    start_time: datetime
    description: Optional[str] = None
    performer: Optional[str] = None
    ticket_classes: List[TicketClassInput]


class ShowUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    description: Optional[str] = None
    performer: Optional[str] = None


class ShowOut(BaseModel):
    id: int
    name: str
    location: str
    start_time: datetime
    total_tickets: int
    available_tickets: int
    description: Optional[str]
    performer: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ShowDetailOut(ShowOut):
    tickets: List[TicketOut]
