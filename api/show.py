from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.show import ShowCreate, ShowOut
from daos.show import ShowDAO
from core.database import get_db

router = APIRouter()

@router.post("/shows", response_model=ShowOut, status_code=status.HTTP_201_CREATED)
def create_show(show_data: ShowCreate, db: Session = Depends(get_db)):
    dao = ShowDAO(db)
    show = dao.create_show_with_tickets(show_data.dict(), price=show_data.price)
    return show