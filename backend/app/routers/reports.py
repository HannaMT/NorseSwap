"""
Reports Router
==============
Students can report listings that violate policies.
Reports go to an admin queue for review.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_verified_user
from app.models.models import User, Listing, Report, ReportReason, ReportStatus
from app.schemas.schemas import ReportCreate, MessageOnlyResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MessageOnlyResponse)
async def create_report(
    body: ReportCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a listing for violating community guidelines."""
    listing = await db.get(Listing, body.listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found.")

    if listing.user_id == current_user.id:
        raise HTTPException(400, "You cannot report your own listing.")

    # Check for duplicate report from same user
    existing = await db.execute(
        select(Report).where(
            Report.reporter_id == current_user.id,
            Report.listing_id == body.listing_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "You have already reported this listing.")

    report = Report(
        reporter_id=current_user.id,
        listing_id=body.listing_id,
        reported_user_id=listing.user_id,
        reason=body.reason,
        description=body.description,
    )
    db.add(report)

    return {"message": "Report submitted. Our team will review it shortly."}