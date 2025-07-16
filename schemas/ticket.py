from pydantic import BaseModel
from typing import Optional


class TicketOut(BaseModel):
    id: int
    status: str
    price: float
    seat: Optional[str]
