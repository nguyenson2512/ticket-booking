from sqlalchemy.orm import Session, joinedload
from models.ticket import Ticket, TicketStatus
from models.show import Show
from schemas.ticket import TicketCreate, TicketUpdate
from typing import List, Optional


class TicketDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def get_tickets_by_show_id(self, show_id: int) -> List[Ticket]:
        """Get all tickets for a specific show"""
        return self.db.query(Ticket).filter(Ticket.show_id == show_id).all()

    def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by its ID"""
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()

    def get_ticket_with_show_details(self, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket with show details loaded"""
        return self.db.query(Ticket).options(
            joinedload(Ticket.show)
        ).filter(Ticket.id == ticket_id).first()

    def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        """Create a new ticket"""
        # Validate that the show exists
        show = self.db.query(Show).filter(Show.id == ticket_data.show_id).first()
        if not show:
            raise ValueError(f"Show with ID {ticket_data.show_id} not found")
        
        # Create the ticket
        ticket = Ticket(
            show_id=ticket_data.show_id,
            price=ticket_data.price,
            seat=ticket_data.seat,
            status=TicketStatus(ticket_data.status)
        )
        
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        
        # Update show ticket counts
        show.total_tickets += 1
        if ticket.status == TicketStatus.available:
            show.available_tickets += 1
        self.db.commit()
        
        return ticket

    def update_ticket(self, ticket_id: int, ticket_update: TicketUpdate) -> Optional[Ticket]:
        """Update a ticket"""
        ticket = self.get_ticket_by_id(ticket_id)
        if not ticket:
            return None
        
        # Store old status for show count updates
        old_status = ticket.status
        
        # Update only the fields that are provided
        update_data = ticket_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value is not None:
                setattr(ticket, field, TicketStatus(value))
            else:
                setattr(ticket, field, value)
        
        self.db.commit()
        self.db.refresh(ticket)
        
        # Update show ticket counts if status changed
        if "status" in update_data and old_status != ticket.status:
            show = self.db.query(Show).filter(Show.id == ticket.show_id).first()
            if show:
                if old_status == TicketStatus.available:
                    show.available_tickets -= 1
                elif ticket.status == TicketStatus.available:
                    show.available_tickets += 1
                self.db.commit()
        
        return ticket

    def delete_ticket(self, ticket_id: int) -> bool:
        """Delete a ticket"""
        ticket = self.get_ticket_by_id(ticket_id)
        if not ticket:
            return False
        
        # Update show ticket counts
        show = self.db.query(Show).filter(Show.id == ticket.show_id).first()
        if show:
            show.total_tickets -= 1
            if ticket.status == TicketStatus.available:
                show.available_tickets -= 1
            self.db.commit()
        
        # Delete the ticket
        self.db.delete(ticket)
        self.db.commit()
        
        return True

    def get_all_tickets(self, skip: int = 0, limit: int = 100) -> List[Ticket]:
        """Get all tickets with pagination"""
        return self.db.query(Ticket).offset(skip).limit(limit).all()

    def get_tickets_by_user_id(self, user_id: int) -> List[Ticket]:
        """Get all tickets for a specific user"""
        return self.db.query(Ticket).filter(Ticket.user_id == user_id).all()

    def get_tickets_by_status(self, status: TicketStatus) -> List[Ticket]:
        """Get all tickets with a specific status"""
        return self.db.query(Ticket).filter(Ticket.status == status).all()
