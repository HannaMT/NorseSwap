"""
Users Router
============
Public and private user profile management.
Includes avatar upload, profile editing, and viewing saved listings.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_verified_user
from app.models.models import User, Listing, ListingStatus, SavedListing
from app.schemas.schemas import UserResponse, UserUpdate, MessageOnlyResponse
from app.utils.cloudinary import upload_images, upload_avatar, delete_image

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the full profile of the currently logged-in user."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile fields."""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    return user


@router.post("/me/avatar", response_model=dict)
async def upload_avatar(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new profile picture."""
    uploaded = await upload_avatar(image, current_user.id)
    if not uploaded:
        raise HTTPException(400, "Image upload failed.")

    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()
    user.avatar_url = uploaded["url"]
    await db.flush()

    return {"avatar_url": user.avatar_url}


@router.get("/me/saved")
async def get_saved_listings(
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all listings the current user has saved."""
    result = await db.execute(
        select(SavedListing)
        .options(
            selectinload(SavedListing.listing).selectinload(Listing.images),
            selectinload(SavedListing.listing).selectinload(Listing.user),
            selectinload(SavedListing.listing).selectinload(Listing.rental_details),
            selectinload(SavedListing.listing).selectinload(Listing.sale_details),
            selectinload(SavedListing.listing).selectinload(Listing.service_details),
        )
        .where(
            SavedListing.user_id == current_user.id,
            # Only show active listings
        )
        .order_by(SavedListing.saved_at.desc())
    )
    saved = result.scalars().all()

    return [
        {
            "saved_at": s.saved_at,
            "listing": {
                "id": s.listing.id,
                "title": s.listing.title,
                "type": s.listing.type,
                "status": s.listing.status,
                "category": s.listing.category,
                "university": s.listing.university,
                "primary_image": next((img.url for img in s.listing.images if img.is_primary), None),
                "price": (
                    s.listing.rental_details.price_per_period if s.listing.rental_details
                    else s.listing.sale_details.price if s.listing.sale_details
                    else s.listing.service_details.price_per_hour if s.listing.service_details
                    else None
                ),
                "owner": {
                    "id": s.listing.user.id,
                    "first_name": s.listing.user.first_name,
                    "avatar_url": s.listing.user.avatar_url,
                },
            },
        }
        for s in saved
    ]


@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a public user profile by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(404, "User not found.")

    # Count their listings and reviews
    listings_result = await db.execute(
        select(Listing).where(Listing.user_id == user_id, Listing.status == ListingStatus.ACTIVE)
    )
    active_listings = listings_result.scalars().all()

    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "university": user.university,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "member_since": user.created_at,
        "active_listings_count": len(active_listings),
    }


@router.get("/{user_id}/listings")
async def get_user_listings(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all active listings by a specific user (public)."""
    result = await db.execute(
        select(Listing)
        .options(
            selectinload(Listing.images),
            selectinload(Listing.rental_details),
            selectinload(Listing.sale_details),
            selectinload(Listing.service_details),
        )
        .where(Listing.user_id == user_id, Listing.status == ListingStatus.ACTIVE)
        .order_by(Listing.created_at.desc())
    )
    return result.scalars().all()