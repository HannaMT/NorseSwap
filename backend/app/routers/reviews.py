"""
Reviews Router
==============
Students can leave reviews after a completed rental, order, or booking.
Each transaction can only be reviewed once (enforced by unique DB constraints).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_verified_user
from app.models.models import User, Review, Listing, NotificationType
from app.schemas.schemas import ReviewCreate, ReviewResponse, UserReviewsResponse
# from app.utils.notifications import push_notification

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a review after a completed transaction."""
    if current_user.id == body.reviewee_id:
        raise HTTPException(400, "You cannot review yourself.")

    # Ensure the listing exists
    listing = await db.get(Listing, body.listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found.")

    # Check for duplicate review
    existing_query = select(Review).where(
        Review.reviewer_id == current_user.id,
        Review.listing_id == body.listing_id,
    )
    if body.rental_id:
        existing_query = existing_query.where(Review.rental_id == body.rental_id)
    elif body.order_id:
        existing_query = existing_query.where(Review.order_id == body.order_id)
    elif body.booking_id:
        existing_query = existing_query.where(Review.booking_id == body.booking_id)

    existing = (await db.execute(existing_query)).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "You have already reviewed this transaction.")

    review = Review(
        listing_id=body.listing_id,
        reviewer_id=current_user.id,
        reviewee_id=body.reviewee_id,
        rating=body.rating,
        comment=body.comment,
        rental_id=body.rental_id,
        order_id=body.order_id,
        booking_id=body.booking_id,
    )
    db.add(review)
    await db.flush()

    # await push_notification(
    #     db,
    #     user_id=body.reviewee_id,
    #     type=NotificationType.NEW_REVIEW,
    #     title="You got a new review! ⭐",
    #     body=f"{current_user.first_name} left you a {body.rating}-star review.",
    #     data={"review_id": review.id, "listing_id": body.listing_id},
    # )

    return {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at,
    }


@router.get("/user/{user_id}", response_model=UserReviewsResponse)
async def get_user_reviews(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews received by a specific user, with average rating."""
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.reviewer))
        .where(Review.reviewee_id == user_id)
        .order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()

    avg = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0.0

    return {
        "reviews": [
            {
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at,
                "reviewer": {
                    "id": r.reviewer.id,
                    "first_name": r.reviewer.first_name,
                    "last_name": r.reviewer.last_name,
                    "avatar_url": r.reviewer.avatar_url,
                },
            }
            for r in reviews
        ],
        "average_rating": avg,
        "total_reviews": len(reviews),
    }


@router.get("/listing/{listing_id}")
async def get_listing_reviews(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews for a specific listing."""
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.reviewer))
        .where(Review.listing_id == listing_id)
        .order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()
    avg = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0.0

    return {
        "reviews": [
            {
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at,
                "reviewer": {
                    "id": r.reviewer.id,
                    "first_name": r.reviewer.first_name,
                    "avatar_url": r.reviewer.avatar_url,
                },
            }
            for r in reviews
        ],
        "average_rating": avg,
        "total_reviews": len(reviews),
    }