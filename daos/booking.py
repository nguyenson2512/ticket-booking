from sqlalchemy.orm import Session, joinedload
from models.booking import Booking, BookingStatus
from models.ticket import Ticket, TicketStatus
from models.show import Show
from models.user import User
from schemas.booking import BookingCreate
from typing import List, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
import json
import os
from services.booking_kafka import booking_producer

class BookingDAO:
    def __init__(self, db: Session):
        self.db = db
        # Initialize Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(redis_url)
        self.booking_ttl = 600  # 10 minutes in seconds

    async def acquire_ticket_lock(self, ticket_id: int, user_id: int) -> bool:
        """Acquire a distributed lock for a ticket using Redis"""
        lock_key = f"ticket_lock:{ticket_id}"
        
        # Try to set the lock with TTL
        result = await self.redis_client.set(
            lock_key, 
            str(user_id), 
            nx=True,  # Only set if key doesn't exist
            ex=self.booking_ttl  # Expire after TTL seconds
        )
        
        return result is not None

    async def release_ticket_lock(self, ticket_id: int) -> bool:
        """Release the distributed lock for a ticket"""
        lock_key = f"ticket_lock:{ticket_id}"
        result = await self.redis_client.delete(lock_key)
        return result > 0

    async def get_ticket_lock_owner(self, ticket_id: int) -> Optional[int]:
        """Get the user ID who currently holds the lock for a ticket"""
        lock_key = f"ticket_lock:{ticket_id}"
        result = await self.redis_client.get(lock_key)
        if result:
            try:
                return int(result.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                return None
        return None

    def create_booking(self, booking_data: BookingCreate, user_id: int) -> Optional[Booking]:
        """Create a new booking"""
        # Check if ticket exists and is available
        ticket = self.db.query(Ticket).filter(
            Ticket.id == booking_data.ticket_id,
            Ticket.status == TicketStatus.available
        ).first()
        
        if not ticket:
            return None
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=self.booking_ttl)
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            ticket_id=booking_data.ticket_id,
            status=BookingStatus.reserved,
            expires_at=expires_at
        )
        
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        
        return booking

    def get_booking_by_id(self, booking_id: int, user_id: int) -> Optional[Booking]:
        """Get a booking by ID for a specific user"""
        return self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.user_id == user_id
        ).first()

    def get_booking_with_details(self, booking_id: int, user_id: int) -> Optional[Booking]:
        """Get a booking with related ticket and show details"""
        return self.db.query(Booking).options(
            joinedload(Booking.ticket).joinedload(Ticket.show)
        ).filter(
            Booking.id == booking_id,
            Booking.user_id == user_id
        ).first()

    def get_user_bookings(self, user_id: int, skip: int = 0, limit: int = 10) -> List[Booking]:
        """Get all bookings for a user with pagination"""
        return self.db.query(Booking).filter(
            Booking.user_id == user_id
        ).order_by(Booking.created_at.desc()).offset(skip).limit(limit).all()

    def count_user_bookings(self, user_id: int) -> int:
        """Count total bookings for a user"""
        return self.db.query(Booking).filter(Booking.user_id == user_id).count()

    def _prepare_booking_data(self, booking: Booking) -> dict:
        """Prepare booking data for Kafka message"""
        return {
            "id": booking.id,
            "user_id": booking.user_id,
            "ticket_id": booking.ticket_id,
            "status": booking.status.value,
            "created_at": booking.created_at.isoformat() if booking.created_at else None,
            "confirmed_at": booking.confirmed_at.isoformat() if booking.confirmed_at else None,
            "cancelled_at": booking.cancelled_at.isoformat() if booking.cancelled_at else None,
            "expires_at": booking.expires_at.isoformat() if booking.expires_at else None
        }

    def _prepare_user_data(self, user: User) -> dict:
        """Prepare user data for Kafka message"""
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }

    def _send_booking_event(self, event_type: str, booking: Booking, user: User):
        """Send booking event to Kafka"""
        try:
            booking_data = self._prepare_booking_data(booking)
            user_data = self._prepare_user_data(user)
            
            booking_producer.send_booking_event(event_type, booking_data, user_data)
        except Exception as e:
            print(f"Failed to send booking event: {e}")

    async def confirm_booking(self, booking_id: int, user_id: int) -> Optional[Booking]:
        """Confirm a booking"""
        booking = self.get_booking_by_id(booking_id, user_id)
        
        if not booking or booking.status != BookingStatus.reserved:
            return None
        
        # Check if booking has expired
        if datetime.utcnow() > booking.expires_at:
            booking.status = BookingStatus.expired
            self.db.commit()
            return None
        
        # Get user data for Kafka message
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Update ticket status to sold
        ticket = self.db.query(Ticket).filter(Ticket.id == booking.ticket_id).first()
        if ticket:
            ticket.status = TicketStatus.sold
            ticket.user_id = user_id
        
        # Update booking status
        booking.status = BookingStatus.confirmed
        booking.confirmed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(booking)
        
        # Send Kafka event
        if user:
            self._send_booking_event("booking_confirmed", booking, user)
        
        # Release the Redis lock
        await self.release_ticket_lock(booking.ticket_id)
        
        return booking

    async def cancel_booking(self, booking_id: int, user_id: int) -> Optional[Booking]:
        """Cancel a booking"""
        booking = self.get_booking_by_id(booking_id, user_id)
        
        if not booking or booking.status != BookingStatus.reserved:
            return None
        
        # Get user data for Kafka message
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Update booking status
        booking.status = BookingStatus.cancelled
        booking.cancelled_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(booking)
        
        # Send Kafka event
        if user:
            self._send_booking_event("booking_cancelled", booking, user)
        
        # Release the Redis lock
        await self.release_ticket_lock(booking.ticket_id)
        
        return booking

    def get_expired_bookings(self) -> List[Booking]:
        """Get all expired bookings that need to be cleaned up"""
        return self.db.query(Booking).filter(
            Booking.status == BookingStatus.reserved,
            Booking.expires_at < datetime.utcnow()
        ).all()

    async def cleanup_expired_bookings(self):
        """Clean up expired bookings and release their locks"""
        expired_bookings = self.get_expired_bookings()
        
        for booking in expired_bookings:
            # Update booking status
            booking.status = BookingStatus.expired
            
            # Release the Redis lock
            await self.release_ticket_lock(booking.ticket_id)
        
        if expired_bookings:
            self.db.commit()

    async def close_redis_connection(self):
        """Close Redis connection"""
        await self.redis_client.close()
