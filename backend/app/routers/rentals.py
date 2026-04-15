"""
Rentals Router
==============
Full rental lifecycle:
  PENDING → APPROVED → ACTIVE (after payment) → RETURNED
  PENDING/APPROVED → CANCELLED
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_verified_user
from app.models.models import (
    User, Listing, Rental, RentalDetails,
    ListingType, ListingStatus, RentalStatus, NotificationType,
)
from app.schemas.schemas import (
    RentalCreate, RentalRespondRequest, RentalReturnRequest, MessageOnlyResponse,
)
from app.utils.email import send_rental_request_email
# from app.utils.notifications import push_notification

router = APIRouter(prefix="/rentals", tags=["Rentals"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def request_rental(
    body: RentalCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a rental request for a listing."""
    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.rental_details), selectinload(Listing.user))
        .where(
            Listing.id == body.listing_id,
            Listing.type == ListingType.RENTAL,
            Listing.status == ListingStatus.ACTIVE,
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(404, "Rental listing not found.")
    if listing.user_id == current_user.id:
        raise HTTPException(400, "You cannot rent your own item.")

    rd = listing.rental_details
    days = max((body.end_date - body.start_date).days, 1)

    if days < rd.min_rental_days:
        raise HTTPException(400, f"Minimum rental period is {rd.min_rental_days} day(s).")
    if rd.max_rental_days and days > rd.max_rental_days:
        raise HTTPException(400, f"Maximum rental period is {rd.max_rental_days} day(s).")

    multipliers = {"HOURLY": days * 24, "DAILY": days, "WEEKLY": -(-days // 7), "MONTHLY": -(-days // 30)}
    total_price = rd.price_per_period * multipliers.get(rd.price_period.value, days)

    rental = Rental(
        listing_id=body.listing_id,
        rental_details_id=rd.id,
        renter_id=current_user.id,
        owner_id=listing.user_id,
        start_date=body.start_date,
        end_date=body.end_date,
        total_price=total_price,
        deposit_amount=rd.deposit_amount,
        notes=body.notes,
    )
    db.add(rental)
    await db.flush()

    # await push_notification(
    #     db,
    #     user_id=listing.user_id,
    #     type=NotificationType.RENTAL_REQUEST,
    #     title="New rental request",
    #     body=f"{current_user.first_name} wants to rent \"{listing.title}\"",
    #     data={"rental_id": rental.id, "listing_id": listing.id},
    # )

    background_tasks.add_task(
        send_rental_request_email,
        listing.user.email,
        listing.user.first_name,
        listing.title,
        f"{current_user.first_name} {current_user.last_name}",
    )

    return {
        "id": rental.id,
        "status": rental.status,
        "total_price": rental.total_price,
        "deposit_amount": rental.deposit_amount,
        "start_date": rental.start_date,
        "end_date": rental.end_date,
    }


@router.get("/my-rentals")
async def get_my_rentals(
    rental_status: Optional[str] = None,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Rentals where current user is the renter."""
    query = (
        select(Rental)
        .options(selectinload(Rental.listing).selectinload(Listing.images), selectinload(Rental.owner))
        .where(Rental.renter_id == current_user.id)
        .order_by(Rental.created_at.desc())
    )
    if rental_status:
        query = query.where(Rental.status == rental_status)
    result = await db.execute(query)
    rentals = result.scalars().all()

    return [
        {
            "id": r.id,
            "status": r.status,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "total_price": r.total_price,
            "deposit_amount": r.deposit_amount,
            "deposit_returned": r.deposit_returned,
            "notes": r.notes,
            "listing": {
                "id": r.listing.id,
                "title": r.listing.title,
                "primary_image": next((img.url for img in r.listing.images if img.is_primary), None),
            },
            "owner": {"id": r.owner.id, "first_name": r.owner.first_name, "avatar_url": r.owner.avatar_url},
        }
        for r in rentals
    ]


@router.get("/my-lendings")
async def get_my_lendings(
    rental_status: Optional[str] = None,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Rentals where current user is the owner/lender."""
    query = (
        select(Rental)
        .options(selectinload(Rental.listing).selectinload(Listing.images), selectinload(Rental.renter))
        .where(Rental.owner_id == current_user.id)
        .order_by(Rental.created_at.desc())
    )
    if rental_status:
        query = query.where(Rental.status == rental_status)
    result = await db.execute(query)
    rentals = result.scalars().all()

    return [
        {
            "id": r.id,
            "status": r.status,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "total_price": r.total_price,
            "deposit_amount": r.deposit_amount,
            "deposit_returned": r.deposit_returned,
            "return_notes": r.return_notes,
            "listing": {
                "id": r.listing.id,
                "title": r.listing.title,
                "primary_image": next((img.url for img in r.listing.images if img.is_primary), None),
            },
            "renter": {"id": r.renter.id, "first_name": r.renter.first_name, "avatar_url": r.renter.avatar_url},
        }
        for r in rentals
    ]


@router.get("/{rental_id}")
async def get_rental(
    rental_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a rental by ID. Only accessible to the renter or owner."""
    result = await db.execute(
        select(Rental)
        .options(
            selectinload(Rental.listing).selectinload(Listing.images),
            selectinload(Rental.renter),
            selectinload(Rental.owner),
        )
        .where(Rental.id == rental_id)
    )
    rental = result.scalar_one_or_none()
    if not rental:
        raise HTTPException(404, "Rental not found.")
    if rental.renter_id != current_user.id and rental.owner_id != current_user.id:
        raise HTTPException(403, "Access denied.")
    return rental


@router.patch("/{rental_id}/respond")
async def respond_to_rental(
    rental_id: str,
    body: RentalRespondRequest,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Owner approves or rejects a pending rental request."""
    result = await db.execute(
        select(Rental).options(selectinload(Rental.listing)).where(Rental.id == rental_id)
    )
    rental = result.scalar_one_or_none()
    if not rental:
        raise HTTPException(404, "Rental not found.")
    if rental.owner_id != current_user.id:
        raise HTTPException(403, "Only the owner can respond to rental requests.")
    if rental.status != RentalStatus.PENDING:
        raise HTTPException(400, "Rental is no longer pending.")

    is_approved = body.action == "approve"
    rental.status = RentalStatus.APPROVED if is_approved else RentalStatus.CANCELLED

    # await push_notification(
    #     db,
    #     user_id=rental.renter_id,
    #     type=NotificationType.RENTAL_APPROVED if is_approved else NotificationType.RENTAL_REQUEST,
    #     title="Rental approved! 🎉" if is_approved else "Rental request declined",
    #     body=(
    #         f"Your request for \"{rental.listing.title}\" was approved. Proceed to payment."
    #         if is_approved else
    #         f"Your request for \"{rental.listing.title}\" was declined."
    #     ),
    #     data={"rental_id": rental_id},
    # )
    return {"id": rental_id, "status": rental.status}


@router.patch("/{rental_id}/return", response_model=MessageOnlyResponse)
async def mark_returned(
    rental_id: str,
    body: RentalReturnRequest,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Owner confirms the item has been returned."""
    result = await db.execute(select(Rental).where(Rental.id == rental_id))
    rental = result.scalar_one_or_none()
    if not rental:
        raise HTTPException(404, "Rental not found.")
    if rental.owner_id != current_user.id:
        raise HTTPException(403, "Only the owner can mark a rental as returned.")
    if rental.status != RentalStatus.ACTIVE:
        raise HTTPException(400, "Rental must be ACTIVE to mark as returned.")

    rental.status = RentalStatus.RETURNED
    rental.return_notes = body.return_notes
    rental.deposit_returned = body.return_deposit

    # await push_notification(
    #     db,
    #     user_id=rental.renter_id,
    #     type=NotificationType.RENTAL_RETURNED,
    #     title="Item returned ✅",
    #     body="Your rental is closed. Please leave a review!",
    #     data={"rental_id": rental_id},
    # )
    # return {"message": "Rental marked as returned."}


@router.patch("/{rental_id}/cancel", response_model=MessageOnlyResponse)
async def cancel_rental(
    rental_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Renter cancels a pending or approved rental."""
    result = await db.execute(select(Rental).where(Rental.id == rental_id))
    rental = result.scalar_one_or_none()
    if not rental:
        raise HTTPException(404, "Rental not found.")
    if rental.renter_id != current_user.id:
        raise HTTPException(403, "Only the renter can cancel.")
    if rental.status not in (RentalStatus.PENDING, RentalStatus.APPROVED):
        raise HTTPException(400, "Cannot cancel a rental in this state.")

    rental.status = RentalStatus.CANCELLED
    return {"message": "Rental cancelled."}