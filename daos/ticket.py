from sqlalchemy.orm import Session
from models.ticket import Ticket
from typing import List

class TicketDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def get_tickets_by_show_id(self, show_id: int) -> List[Ticket]:
        """Get all tickets for a specific show"""
        return self.db.query(Ticket).filter(Ticket.show_id == show_id).all()

