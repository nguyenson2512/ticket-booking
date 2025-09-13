from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models.user import User
from models.ticket import Ticket, TicketStatus
from schemas.ticket import TicketOut, TicketCreate, TicketUpdate, TicketDetailOut
from daos.ticket import TicketDAO
from core.database import get_db
from services.auth_service import get_current_user
from typing import List, Optional

router = APIRouter()


def require_admin_role(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return current_user


@router.get("/tickets/{ticket_id}", response_model=TicketDetailOut)
def get_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific ticket"""
    dao = TicketDAO(db)
    ticket = dao.get_ticket_with_show_details(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Create response with show details
    response_data = {
        "id": ticket.id,
        "show_id": ticket.show_id,
        "user_id": ticket.user_id,
        "status": ticket.status.value,
        "price": float(ticket.price),
        "seat": ticket.seat,
        "show_name": ticket.show.name if ticket.show else None,
        "show_location": ticket.show.location if ticket.show else None,
        "show_start_time": ticket.show.start_time.isoformat() if ticket.show else None
    }
    
    return response_data


@router.get("/tickets", response_model=List[TicketOut])
def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=1000),
    show_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a list of tickets with optional filtering"""
    dao = TicketDAO(db)
    
    # Build query based on filters
    query = db.query(Ticket)
    
    if show_id:
        query = query.filter(Ticket.show_id == show_id)
    
    if user_id:
        query = query.filter(Ticket.user_id == user_id)
    
    if status:
        try:
            ticket_status = TicketStatus(status)
            query = query.filter(Ticket.status == ticket_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in TicketStatus]}"
            )
    
    tickets = query.offset(skip).limit(limit).all()
    return tickets


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """Create a new ticket (admin only)"""
    dao = TicketDAO(db)
    
    try:
        # Validate status
        if ticket_data.status not in [s.value for s in TicketStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in TicketStatus]}"
            )
        
        ticket = dao.create_ticket(ticket_data)
        return ticket
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )


@router.put("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """Update ticket information (admin only)"""
    dao = TicketDAO(db)
    
    # Validate status if provided
    if ticket_update.status and ticket_update.status not in [s.value for s in TicketStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {[s.value for s in TicketStatus]}"
        )
    
    ticket = dao.update_ticket(ticket_id, ticket_update)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return ticket


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """Delete a ticket (admin only)"""
    dao = TicketDAO(db)
    
    success = dao.delete_ticket(ticket_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )


@router.get("/tickets/user/{user_id}", response_model=List[TicketOut])
def get_user_tickets(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tickets for a specific user"""
    dao = TicketDAO(db)
    tickets = dao.get_tickets_by_user_id(user_id)
    return tickets


@router.get("/tickets/status/{status}", response_model=List[TicketOut])
def get_tickets_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tickets with a specific status"""
    try:
        ticket_status = TicketStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {[s.value for s in TicketStatus]}"
        )
    
    dao = TicketDAO(db)
    tickets = dao.get_tickets_by_status(ticket_status)
    return tickets
