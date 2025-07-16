from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.show import ShowCreate, ShowOut
from daos.show import ShowDAO
from core.database import get_db

router = APIRouter()


@router.post("/shows", response_model=ShowOut, status_code=status.HTTP_201_CREATED)
async def create_show(show_data: ShowCreate, db: Session = Depends(get_db)):
    try:
        total_tickets = sum(
            ticket_class.quantity for ticket_class in show_data.ticket_classes)
        if total_tickets == 0:
            raise HTTPException(
                status_code=400, detail="At least one ticket must be created")

        # Create the show
        dao = ShowDAO(db)
        show = dao.create_show_with_tickets(
            show_data, total_tickets=total_tickets)
        return show
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating show: {str(e)}")
