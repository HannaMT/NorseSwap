"""
Services Router
===============
Handles bookings for service listings (tutoring, rides, etc.)

Flow: PENDING → CONFIRMED → COMPLETED
      PENDING/CONFIRMED → CANCELLED
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_verified_user
from app.models.models import (
    User, Listing, ServiceBooking, ServiceDetails,
    ListingType, ListingStatus, BookingStatus, NotificationType,
)
from app.schemas.schemas import BookingCreate, MessageOnlyResponse
# from app.utils.notifications import push_notification

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Book a service from another student."""
    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.service_details))
        .where(
            Listing.id == body.listing_id,
            Listing.type == ListingType.SERVICE,
            Listing.status == ListingStatus.ACTIVE,
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(404, "Service listing not found.")
    if listing.user_id == current_user.id:
        raise HTTPException(400, "You cannot book your own service.")

    sd = listing.service_details
    if sd is None:
        raise HTTPException(400, "Service listing has no service details.")
    if body.duration_hours < sd.min_hours:
        raise HTTPException(400, f"Minimum booking is {sd.min_hours} hour(s).")
    if sd.max_hours and body.duration_hours > sd.max_hours:
        raise HTTPException(400, f"Maximum booking is {sd.max_hours} hour(s).")

    total_amount = sd.price_per_hour * body.duration_hours

    booking = ServiceBooking(
        listing_id=body.listing_id,
        service_details_id=sd.id,
        client_id=current_user.id,
        provider_id=listing.user_id,
        scheduled_at=body.scheduled_at,
        duration_hours=body.duration_hours,
        total_amount=total_amount,
        notes=body.notes,
    )
    db.add(booking)
    await db.flush()

    # await push_notification(
    #     db,
    #     user_id=listing.user_id,
    #     type=NotificationType.BOOKING_REQUEST,
    #     title="New booking request 📅",
    #     body=f"{current_user.first_name} booked \"{listing.title}\" for {body.duration_hours} hour(s).",
    #     data={"booking_id": booking.id},
    # )

    return {
        "id": booking.id,
        "status": booking.status,
        "scheduled_at": booking.scheduled_at,
        "duration_hours": booking.duration_hours,
        "total_amount": booking.total_amount,
    }


@router.get("/my-bookings")
async def get_my_bookings(
    booking_status: Optional[str] = None,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookings where current user is the client."""
    query = (
        select(ServiceBooking)
        .options(
            selectinload(ServiceBooking.listing).selectinload(Listing.images),
            selectinload(ServiceBooking.provider),
        )
        .where(ServiceBooking.client_id == current_user.id)
        .order_by(ServiceBooking.created_at.desc())
    )
    if booking_status:
        query = query.where(ServiceBooking.status == booking_status)

    result = await db.execute(query)
    bookings = result.scalars().all()

    return [
        {
            "id": b.id,
            "status": b.status,
            "scheduled_at": b.scheduled_at,
            "duration_hours": b.duration_hours,
            "total_amount": b.total_amount,
            "notes": b.notes,
            "created_at": b.created_at,
            "listing": {
                "id": b.listing.id,
                "title": b.listing.title,
                "primary_image": next((img.url for img in b.listing.images if img.is_primary), None),
            },
            "provider": {
                "id": b.provider.id,
                "first_name": b.provider.first_name,
                "avatar_url": b.provider.avatar_url,
            },
        }
        for b in bookings
    ]


@router.get("/my-services")
async def get_my_services(
    booking_status: Optional[str] = None,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookings where current user is the service provider."""
    query = (
        select(ServiceBooking)
        .options(
            selectinload(ServiceBooking.listing),
            selectinload(ServiceBooking.client),
        )
        .where(ServiceBooking.provider_id == current_user.id)
        .order_by(ServiceBooking.scheduled_at.asc())
    )
    if booking_status:
        query = query.where(ServiceBooking.status == booking_status)

    result = await db.execute(query)
    bookings = result.scalars().all()

    return [
        {
            "id": b.id,
            "status": b.status,
            "scheduled_at": b.scheduled_at,
            "duration_hours": b.duration_hours,
            "total_amount": b.total_amount,
            "notes": b.notes,
            "listing": {"id": b.listing.id, "title": b.listing.title},
            "client": {
                "id": b.client.id,
                "first_name": b.client.first_name,
                "avatar_url": b.client.avatar_url,
            },
        }
        for b in bookings
    ]


@router.patch("/{booking_id}/confirm", response_model=MessageOnlyResponse)
async def confirm_booking(
    booking_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Provider confirms a booking."""
    result = await db.execute(
        select(ServiceBooking).options(selectinload(ServiceBooking.listing))
        .where(ServiceBooking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found.")
    if booking.provider_id != current_user.id:
        raise HTTPException(403, "Only the provider can confirm a booking.")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(400, "Booking is not pending.")

    booking.status = BookingStatus.CONFIRMED
    # await push_notification(
    #     db,
    #     user_id=booking.client_id,
    #     type=NotificationType.BOOKING_CONFIRMED,
    #     title="Booking confirmed! ✅",
    #     body=f"Your booking for \"{booking.listing.title}\" is confirmed.",
    #     data={"booking_id": booking_id},
    # )
    return {"message": "Booking confirmed."}


@router.patch("/{booking_id}/complete", response_model=MessageOnlyResponse)
async def complete_booking(
    booking_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Client marks a service as completed."""
    result = await db.execute(select(ServiceBooking).where(ServiceBooking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found.")
    if booking.client_id != current_user.id:
        raise HTTPException(403, "Only the client can mark as completed.")
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(400, "Booking must be confirmed first.")

    booking.status = BookingStatus.COMPLETED
    # await push_notification(
    #     db,
    #     user_id=booking.provider_id,
    #     type=NotificationType.PAYMENT_RECEIVED,
    #     title="Service completed! 🎉",
    #     body="Great work! The client marked your service as complete.",
    #     data={"booking_id": booking_id},
    # )
    return {"message": "Booking marked as complete."}


@router.patch("/{booking_id}/cancel", response_model=MessageOnlyResponse)
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Either party can cancel a pending or confirmed booking."""
    result = await db.execute(select(ServiceBooking).where(ServiceBooking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found.")
    if booking.client_id != current_user.id and booking.provider_id != current_user.id:
        raise HTTPException(403, "Access denied.")
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise HTTPException(400, "Cannot cancel a booking in this state.")

    booking.status = BookingStatus.CANCELLED

    # Notify the other party
    notify_user = booking.provider_id if current_user.id == booking.client_id else booking.client_id
    # await push_notification(
    #     db,
    #     user_id=notify_user,
    #     type=NotificationType.BOOKING_REQUEST,
    #     title="Booking cancelled",
    #     body="A booking was cancelled.",
    #     data={"booking_id": booking_id},
    # )
    return {"message": "Booking cancelled."}