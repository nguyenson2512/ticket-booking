from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models.user import User
from models.booking import Booking, BookingStatus
from models.ticket import Ticket, TicketStatus
from schemas.booking import (
    BookingCreate, 
    BookingOut, 
    BookingDetailOut, 
    BookingListResponse,
    BookingConfirmRequest,
    BookingCancelRequest
)
from daos.booking import BookingDAO
from core.database import get_db
from services.auth_service import get_current_user
from typing import List
import math

router = APIRouter()


@router.post("/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new booking with distributed locking"""
    dao = BookingDAO(db)
    
    try:
        # Check if ticket exists and is available
        ticket = db.query(Ticket).filter(
            Ticket.id == booking_data.ticket_id,
            Ticket.status == TicketStatus.available
        ).first()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found or not available"
            )
        
        # Try to acquire distributed lock
        lock_acquired = await dao.acquire_ticket_lock(booking_data.ticket_id, current_user.id)
        
        if not lock_acquired:
            # Check if another user has the lock
            lock_owner = await dao.get_ticket_lock_owner(booking_data.ticket_id)
            if lock_owner and lock_owner != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ticket is currently being booked by another user"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Unable to reserve ticket at this time"
                )
        
        # Create the booking
        booking = dao.create_booking(booking_data, current_user.id)
        
        if not booking:
            # Release lock if booking creation failed
            await dao.release_ticket_lock(booking_data.ticket_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create booking"
            )
        
        # Send Kafka event for booking creation
        dao._send_booking_event("booking_created", booking, current_user)
        
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        # Release lock on any error
        await dao.release_ticket_lock(booking_data.ticket_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating booking: {str(e)}"
        )


@router.get("/bookings", response_model=BookingListResponse)
async def list_user_bookings(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List current user's bookings with pagination"""
    dao = BookingDAO(db)
    
    # Calculate pagination
    skip = (page - 1) * limit
    total_count = dao.count_user_bookings(current_user.id)
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
    
    # Get bookings
    bookings = dao.get_user_bookings(current_user.id, skip, limit)
    
    return BookingListResponse(
        total_count=total_count,
        current_page=page,
        total_pages=total_pages,
        data=bookings
    )


@router.get("/bookings/{booking_id}", response_model=BookingDetailOut)
async def get_booking_details(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific booking"""
    dao = BookingDAO(db)
    
    booking = dao.get_booking_with_details(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Build detailed response
    response_data = {
        "id": booking.id,
        "user_id": booking.user_id,
        "ticket_id": booking.ticket_id,
        "status": booking.status.value,
        "created_at": booking.created_at,
        "confirmed_at": booking.confirmed_at,
        "cancelled_at": booking.cancelled_at,
        "expires_at": booking.expires_at,
        "ticket_price": float(booking.ticket.price) if booking.ticket else None,
        "ticket_seat": booking.ticket.seat if booking.ticket else None,
        "ticket_status": booking.ticket.status.value if booking.ticket else None,
        "show_name": booking.ticket.show.name if booking.ticket and booking.ticket.show else None,
        "show_location": booking.ticket.show.location if booking.ticket and booking.ticket.show else None,
        "show_start_time": booking.ticket.show.start_time if booking.ticket and booking.ticket.show else None
    }
    
    return response_data


@router.post("/bookings/{booking_id}/confirm", response_model=BookingOut)
async def confirm_booking(
    booking_id: int,
    confirm_data: BookingConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm a booking (after the hold/seat reservation step)"""
    dao = BookingDAO(db)
    
    try:
        booking = await dao.confirm_booking(booking_id, current_user.id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or cannot be confirmed"
            )
        
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming booking: {str(e)}"
        )


@router.post("/bookings/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: int,
    cancel_data: BookingCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a reserved booking"""
    dao = BookingDAO(db)
    
    try:
        booking = await dao.cancel_booking(booking_id, current_user.id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or cannot be cancelled"
            )
        
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling booking: {str(e)}"
        )


@router.post("/bookings/cleanup-expired", status_code=status.HTTP_200_OK)
async def cleanup_expired_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clean up expired bookings (admin utility endpoint)"""
    # Check if user has admin role
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    
    dao = BookingDAO(db)
    
    try:
        await dao.cleanup_expired_bookings()
        return {"message": "Expired bookings cleaned up successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up expired bookings: {str(e)}"
        )
