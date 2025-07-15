from pydantic import BaseModel, Field, condecimal
from typing import Optional
from datetime import datetime

class ShowCreate(BaseModel):
    name: str
    location: str
    start_time: datetime
    total_tickets: int = Field(..., gt=0)
    description: Optional[str] = None
    performer: Optional[str] = None
    price: condecimal(gt=0)

class ShowOut(BaseModel):
    id: int
    name: str
    location: str
    start_time: datetime
    total_tickets: int
    available_tickets: int
    description: Optional[str]
    performer: Optional[str]

    class Config:
        orm_mode = True