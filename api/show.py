import json
from typing import Any, Dict, List
from daos.ticket import TicketDAO
from fastapi import APIRouter, Depends, HTTPException, status
from models.show import Show
from models.user import User
from schemas.ticket import TicketOut
from sqlalchemy.orm import Session, joinedload
from schemas.show import ShowCreate, ShowDetailOut, ShowOut, ShowUpdate
from daos.show import ShowDAO
from core.database import get_db
from fastapi import Query
from core.redis import redis_client
from core.elasticsearch import es_client
from services.auth_service import get_current_user

router = APIRouter()


def require_admin_role(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return current_user


@router.post("/shows", response_model=ShowOut, status_code=status.HTTP_201_CREATED)
async def create_show(
    show_data: ShowCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
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


@router.put("/shows/{show_id}", response_model=ShowOut)
async def update_show(
    show_id: int,
    show_update: ShowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """Update a show (admin only)"""
    dao = ShowDAO(db)
    show = dao.update_show(show_id, show_update)
    
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found"
        )
    
    # Clear cache for this show
    await redis_client.delete(f"show_{show_id}")
    
    return show


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
    cached_show = await redis_client.get(f"show_{show_id}")

    if cached_show:
        data = json.loads(cached_show)
        return data
    show = db.query(Show).filter(Show.id == show_id).first()

    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    await redis_client.set(f"show_{show_id}", ShowOut.model_validate(show).model_dump_json())
    return show

@router.get("/shows/{show_id}/tickets", response_model=List[TicketOut])
def get_tickets_by_show(
    show_id: int,
    db: Session = Depends(get_db)
):
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found"
        )

    tickets = TicketDAO(db).get_tickets_by_show_id(show_id)

    return tickets
