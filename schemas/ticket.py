from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal


class TicketOut(BaseModel):
    id: int
    show_id: int
    user_id: Optional[int]
    status: str
    price: float
    seat: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    show_id: int
    price: Decimal = Field(..., gt=0, description="Ticket price must be greater than 0")
    seat: Optional[str] = None
    status: str = "available"


class TicketUpdate(BaseModel):
    price: Optional[Decimal] = Field(None, gt=0, description="Ticket price must be greater than 0")
    seat: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None


class TicketDetailOut(TicketOut):
    show_name: Optional[str] = None
    show_location: Optional[str] = None
    show_start_time: Optional[str] = None
