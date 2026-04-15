"""
Notifications Router
====================
In-app notification management.
Notifications are created by other routers (rentals, orders, etc.)
and read/managed here.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.dependencies import get_verified_user
from app.models.models import User, Notification
from app.schemas.schemas import MessageOnlyResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's notifications, newest first."""
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    if unread_only:
        query = query.where(Notification.is_read == False)

    result = await db.execute(query)
    notifications = result.scalars().all()

    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "data": n.data,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the count of unread notifications (for badge display)."""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    count = result.scalar()
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=MessageOnlyResponse)
async def mark_one_read(
    notification_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "Notification not found.")

    notification.is_read = True
    return {"message": "Notification marked as read."}


@router.patch("/read-all", response_model=MessageOnlyResponse)
async def mark_all_read(
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    return {"message": "All notifications marked as read."}


@router.delete("/{notification_id}", response_model=MessageOnlyResponse)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "Notification not found.")

    await db.delete(notification)
    return {"message": "Notification deleted."}