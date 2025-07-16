from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from models.show import Show
from sqlalchemy.orm import Session, joinedload
from schemas.show import ShowCreate, ShowDetailOut, ShowOut
from daos.show import ShowDAO
from core.database import get_db
from fastapi import Query
from core.redis import redis_client

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


@router.get("/shows")
def list_shows(
    page: int = Query(1, ge=1),
    limit: int = Query(10, gt=0),
    db: Session = Depends(get_db)
):
    total_record = db.query(Show).count()
    offset = (page - 1) * limit
    shows = db.query(Show).offset(offset).limit(limit).all()
    return {
        "total_record": total_record,
        "current_page": page,
        "data": shows
    }

# , response_model=ShowDetailOut


@router.get("/shows/{show_id}")
async def get_show_detail(show_id: int, db: Session = Depends(get_db)):
    cached_item = await redis_client.get(f"item_{show_id}")

    if cached_item:
        print(cached_item)
        return {"show_id": show_id, "cached": True, "data": cached_item.decode('utf-8')}
    show = db.query(Show).options(joinedload(Show.tickets)
                                  ).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    await redis_client.set(f"show_{show_id}", show)
    return {"show_id": show_id, "cached": False, "data": show}
    # return show
