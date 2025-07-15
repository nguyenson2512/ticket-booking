from sqlalchemy.orm import Session
from models.show import Show
from models.ticket import Ticket, TicketStatus

class ShowDAO:
    def __init__(self, db: Session):
        self.db = db

    def create_show_with_tickets(self, show_data: dict, price: float):
        show = Show(
            name=show_data["name"],
            location=show_data["location"],
            start_time=show_data["start_time"],
            total_tickets=show_data["total_tickets"],
            available_tickets=show_data["total_tickets"],
            description=show_data.get("description"),
            performer=show_data.get("performer"),
        )
        self.db.add(show)
        self.db.flush()

        tickets = []
        for i in range(show.total_tickets):
            ticket = Ticket(
                show_id=show.id,
                price=price,
                seat=str(i + 1),  # Ví dụ ghế "1", "2", ...
                status=TicketStatus.available
            )
            tickets.append(ticket)
            self.db.add(ticket)

        self.db.commit()
        self.db.refresh(show)
        return show
