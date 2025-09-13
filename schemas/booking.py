from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class BookingCreate(BaseModel):
    ticket_id: int = Field(..., description="ID of the ticket to book")


class BookingOut(BaseModel):
    id: int
    user_id: int
    ticket_id: int
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingDetailOut(BookingOut):
    ticket_price: Optional[float] = None
    ticket_seat: Optional[str] = None
    ticket_status: Optional[str] = None
    show_name: Optional[str] = None
    show_location: Optional[str] = None
    show_start_time: Optional[datetime] = None


class BookingListResponse(BaseModel):
    total_count: int
    current_page: int
    total_pages: int
    data: list[BookingOut]


class BookingConfirmRequest(BaseModel):
    pass  # No additional data needed for confirmation


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = None  # Optional cancellation reason
