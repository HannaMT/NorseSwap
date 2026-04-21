"""
Orders Router
=============
Handles the buy/sell flow for marketplace listings (type=SALE).

Flow: PENDING → PAID (after Stripe) → MEETUP_SCHEDULED → COMPLETED
                                    → CANCELLED / DISPUTED / REFUNDED
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_verified_user
from app.models.models import (
    User, Listing, Order, SaleDetails,
    ListingType, ListingStatus, OrderStatus, NotificationType,
)
from app.schemas.schemas import OrderCreate, MessageOnlyResponse
# from app.utils.notifications import push_notification

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a buy order for a sale listing."""
    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.sale_details))
        .where(
            Listing.id == body.listing_id,
            Listing.type == ListingType.SALE,
            Listing.status == ListingStatus.ACTIVE,
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(404, "Listing not found or not available.")
    if listing.user_id == current_user.id:
        raise HTTPException(400, "You cannot buy your own item.")
    if listing.sale_details.quantity < body.quantity:
        raise HTTPException(400, f"Only {listing.sale_details.quantity} unit(s) available.")

    total = listing.sale_details.price * body.quantity

    order = Order(
        listing_id=body.listing_id,
        sale_details_id=listing.sale_details.id,
        buyer_id=current_user.id,
        seller_id=listing.user_id,
        price=listing.sale_details.price,
        quantity=body.quantity,
        total_amount=total,
        notes=body.notes,
    )
    db.add(order)
    await db.flush()

    # await push_notification(
    #     db,
    #     user_id=listing.user_id,
    #     type=NotificationType.ORDER_RECEIVED,
    #     title="New purchase request 🛒",
    #     body=f"{current_user.first_name} wants to buy \"{listing.title}\"",
    #     data={"order_id": order.id, "listing_id": listing.id},
    # )
    background_tasks.add_task(
        send_order_received_email,
        listing.user.email,
        listing.user.first_name,
        listing.title,
        f"{current_user.first_name} {current_user.last_name}"
    )
    # return {
    #     "id": order.id,
    #     "status": order.status,
    #     "price": order.price,
    #     "quantity": order.quantity,
    #     "total_amount": order.total_amount,
    # }
    return order


@router.get("/my-orders")
async def get_my_orders(
    order_status: Optional[str] = None,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """All orders where current user is the buyer."""
    query = (
        select(Order)
        .options(
            selectinload(Order.listing).selectinload(Listing.images),
            selectinload(Order.seller),
        )
        .where(Order.buyer_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    if order_status:
        query = query.where(Order.status == order_status)

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "status": o.status,
            "price": o.price,
            "quantity": o.quantity,
            "total_amount": o.total_amount,
            "meetup_location": o.meetup_location,
            "meetup_time": o.meetup_time,
            "notes": o.notes,
            "created_at": o.created_at,
            "listing": {
                "id": o.listing.id,
                "title": o.listing.title,
                "primary_image": next((img.url for img in o.listing.images if img.is_primary), None),
            },
            "seller": {
                "id": o.seller.id,
                "first_name": o.seller.first_name,
                "avatar_url": o.seller.avatar_url,
            },
        }
        for o in orders
    ]


@router.get("/my-sales")
async def get_my_sales(
    order_status: Optional[str] = None,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """All orders where current user is the seller."""
    query = (
        select(Order)
        .options(
            selectinload(Order.listing).selectinload(Listing.images),
            selectinload(Order.buyer),
        )
        .where(Order.seller_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    if order_status:
        query = query.where(Order.status == order_status)

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "status": o.status,
            "price": o.price,
            "quantity": o.quantity,
            "total_amount": o.total_amount,
            "meetup_location": o.meetup_location,
            "meetup_time": o.meetup_time,
            "notes": o.notes,
            "created_at": o.created_at,
            "listing": {
                "id": o.listing.id,
                "title": o.listing.title,
                "primary_image": next((img.url for img in o.listing.images if img.is_primary), None),
            },
            "buyer": {
                "id": o.buyer.id,
                "first_name": o.buyer.first_name,
                "avatar_url": o.buyer.avatar_url,
            },
        }
        for o in orders
    ]


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single order. Only buyer or seller can view it."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.listing).selectinload(Listing.images),
            selectinload(Order.buyer),
            selectinload(Order.seller),
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(403, "Access denied.")
    return order


@router.patch("/{order_id}/schedule-meetup")
async def schedule_meetup(
    order_id: str,
    meetup_location: str,
    meetup_time: datetime,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Seller proposes a meetup location and time."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found.")
    if order.seller_id != current_user.id:
        raise HTTPException(403, "Only the seller can schedule a meetup.")
    if order.status not in (OrderStatus.PENDING, OrderStatus.PAID):
        raise HTTPException(400, "Cannot schedule meetup for this order status.")

    order.meetup_location = meetup_location
    order.meetup_time = meetup_time
    order.status = OrderStatus.MEETUP_SCHEDULED

    # await push_notification(
    #     db,
    #     user_id=order.buyer_id,
    #     type=NotificationType.ORDER_CONFIRMED,
    #     title="Meetup scheduled 📍",
    #     body=f"Meet at {meetup_location}",
    #     data={"order_id": order_id},
    # )
    return {"id": order_id, "status": order.status, "meetup_location": meetup_location, "meetup_time": meetup_time}


@router.patch("/{order_id}/complete", response_model=MessageOnlyResponse)
async def complete_order(
    order_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Buyer confirms they received the item."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "Only the buyer can confirm receipt.")
    if order.status != OrderStatus.MEETUP_SCHEDULED:
        raise HTTPException(400, "Order must have a scheduled meetup first.")

    order.status = OrderStatus.COMPLETED

    # await push_notification(
    #     db,
    #     user_id=order.seller_id,
    #     type=NotificationType.PAYMENT_RECEIVED,
    #     title="Sale completed! 🎉",
    #     body="The buyer confirmed receipt. Please leave a review.",
    #     data={"order_id": order_id},
    # )
    return {"message": "Order marked as complete."}


@router.patch("/{order_id}/cancel", response_model=MessageOnlyResponse)
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Buyer cancels a pending order."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "Only the buyer can cancel.")
    if order.status != OrderStatus.PENDING:
        raise HTTPException(400, "Only pending orders can be cancelled.")

    order.status = OrderStatus.CANCELLED
    return {"message": "Order cancelled."}