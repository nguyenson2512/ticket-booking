from sqlalchemy.orm import Session
from models.show import Show
from models.ticket import Ticket, TicketStatus
from schemas.show import ShowUpdate


class ShowDAO:
    def __init__(self, db: Session):
        self.db = db

    def create_show_with_tickets(self, show_data, total_tickets: int):
        show = Show(
            name=show_data.name,
            location=show_data.location,
            start_time=show_data.start_time,
            total_tickets=total_tickets,
            available_tickets=total_tickets,
            description=show_data.description,
            performer=show_data.performer,
        )
        self.db.add(show)
        self.db.flush()  # Get the show ID without committing

        for ticket_class in show_data.ticket_classes:
            for i in range(ticket_class.quantity):
                # Generate seat identifier (e.g., "VIP-001", "Regular-002")
                seat = f"{ticket_class.ticket_class}-{i+1:03d}"
                db_ticket = Ticket(
                    show_id=show.id,
                    status=TicketStatus.available,
                    price=ticket_class.price,
                    seat=seat
                )
                self.db.add(db_ticket)

        self.db.commit()
        self.db.refresh(show)
        return show

    def get_show_by_id(self, show_id: int):
        """Get a show by its ID"""
        return self.db.query(Show).filter(Show.id == show_id).first()

    def update_show(self, show_id: int, show_update: ShowUpdate):
        """Update a show with the provided data"""
        show = self.get_show_by_id(show_id)
        if not show:
            return None
        
        # Update only the fields that are provided
        update_data = show_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(show, field, value)
        
        self.db.commit()
        self.db.refresh(show)
        return show
