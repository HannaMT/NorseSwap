"""
LEARN: Database Models (SQLAlchemy)
====================================
These are the Python equivalent of your Prisma schema.
Each class = one database table.

Key differences from Prisma:
  - Instead of `model User { ... }` you write `class User(Base): ...`
  - Column types are explicit: String, Integer, Float, Boolean, DateTime
  - Relationships are defined with `relationship()` instead of Prisma's implicit ones
  - `Mapped[str]` is a type hint that tells SQLAlchemy AND your IDE the column type

The `__tablename__` attribute is the actual table name in PostgreSQL.
"""

import uuid
from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import (
    String, Boolean, Float, Integer, DateTime, Text,
    ForeignKey, Enum as SAEnum, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.core.database import Base


# ─── ENUMS ────────────────────────────────────
# LEARN: Python enums map to PostgreSQL ENUM types
# Same as `enum ListingType { RENTAL SALE SERVICE }` in Prisma

class ListingType(str, enum.Enum):
    RENTAL = "RENTAL"
    SALE = "SALE"
    SERVICE = "SERVICE"

class ListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SOLD = "SOLD"
    DELETED = "DELETED"

class ListingCondition(str, enum.Enum):
    NEW = "NEW"
    LIKE_NEW = "LIKE_NEW"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"

class PricePeriod(str, enum.Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

class RentalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    MEETUP_SCHEDULED = "MEETUP_SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"

class ServiceCategory(str, enum.Enum):
    TUTORING = "TUTORING"
    RIDES = "RIDES"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    DESIGN = "DESIGN"
    CODING = "CODING"
    WRITING = "WRITING"
    FITNESS = "FITNESS"
    MUSIC = "MUSIC"
    OTHER = "OTHER"

class NotificationType(str, enum.Enum):
    NEW_MESSAGE = "NEW_MESSAGE"
    RENTAL_REQUEST = "RENTAL_REQUEST"
    RENTAL_APPROVED = "RENTAL_APPROVED"
    RENTAL_RETURNED = "RENTAL_RETURNED"
    ORDER_RECEIVED = "ORDER_RECEIVED"
    ORDER_CONFIRMED = "ORDER_CONFIRMED"
    BOOKING_REQUEST = "BOOKING_REQUEST"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    NEW_REVIEW = "NEW_REVIEW"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"

class ReportReason(str, enum.Enum):
    SPAM = "SPAM"
    INAPPROPRIATE = "INAPPROPRIATE"
    SCAM = "SCAM"
    WRONG_CATEGORY = "WRONG_CATEGORY"
    ALREADY_SOLD = "ALREADY_SOLD"
    OTHER = "OTHER"

class ReportStatus(str, enum.Enum):
    OPEN = "OPEN"
    REVIEWING = "REVIEWING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


# ─────────────────────────────────────────────
# USER & AUTH MODELS
# ─────────────────────────────────────────────

class User(Base):
    """
    LEARN: This is the User table.
    
    `Mapped[str]` = required column (NOT NULL in SQL)
    `Mapped[Optional[str]]` = nullable column (NULL allowed)
    `mapped_column(default=...)` = default value
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    university: Mapped[str] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    stripe_account_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    service_bookings_as_client: Mapped[List["ServiceBooking"]] = relationship(
    "ServiceBooking",
    foreign_keys="ServiceBooking.client_id",
    back_populates="client",)

    service_bookings_as_provider: Mapped[List["ServiceBooking"]] = relationship(
    "ServiceBooking",
    foreign_keys="ServiceBooking.provider_id",
    back_populates="provider",)
    # LEARN: `relationship()` lets you access related objects like:
    #   user.listings  → list of all listings by this user
    #   listing.user   → the user who created the listing
    # `back_populates` connects the two sides of the relationship
    listings: Mapped[List["Listing"]] = relationship("Listing", back_populates="user")
    rentals_as_renter: Mapped[List["Rental"]] = relationship("Rental", foreign_keys="Rental.renter_id", back_populates="renter")
    rentals_as_owner: Mapped[List["Rental"]] = relationship("Rental", foreign_keys="Rental.owner_id", back_populates="owner")
    orders_as_buyer: Mapped[List["Order"]] = relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer")
    orders_as_seller: Mapped[List["Order"]] = relationship("Order", foreign_keys="Order.seller_id", back_populates="seller")
    sent_messages: Mapped[List["Message"]] = relationship("Message", back_populates="sender")
    conversations: Mapped[List["ConversationParticipant"]] = relationship("ConversationParticipant", back_populates="user")
    reviews_given: Mapped[List["Review"]] = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer")
    reviews_received: Mapped[List["Review"]] = relationship("Review", foreign_keys="Review.reviewee_id", back_populates="reviewee")
    saved_listings: Mapped[List["SavedListing"]] = relationship("SavedListing", back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")
    email_verification: Mapped[Optional["EmailVerification"]] = relationship("EmailVerification", back_populates="user", uselist=False)
    password_resets: Mapped[List["PasswordReset"]] = relationship("PasswordReset", back_populates="user")


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="email_verification")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="password_resets")


# ─────────────────────────────────────────────
# LISTINGS
# ─────────────────────────────────────────────

class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    type: Mapped[ListingType] = mapped_column(SAEnum(ListingType))
    status: Mapped[ListingStatus] = mapped_column(SAEnum(ListingStatus), default=ListingStatus.ACTIVE)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), index=True)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    university: Mapped[str] = mapped_column(String(200), index=True)
    allow_other_campuses: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="listings")
    images: Mapped[List["ListingImage"]] = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    rental_details: Mapped[Optional["RentalDetails"]] = relationship("RentalDetails", back_populates="listing", uselist=False, cascade="all, delete-orphan")
    sale_details: Mapped[Optional["SaleDetails"]] = relationship("SaleDetails", back_populates="listing", uselist=False, cascade="all, delete-orphan")
    service_details: Mapped[Optional["ServiceDetails"]] = relationship("ServiceDetails", back_populates="listing", uselist=False, cascade="all, delete-orphan")
    rentals: Mapped[List["Rental"]] = relationship("Rental", back_populates="listing")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="listing")
    saved_by: Mapped[List["SavedListing"]] = relationship("SavedListing", back_populates="listing")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="listing")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="listing")


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String)
    public_id: Mapped[str] = mapped_column(String)  # Cloudinary public_id
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="images")


# ─────────────────────────────────────────────
# RENTAL DETAILS & TRANSACTIONS
# ─────────────────────────────────────────────

class RentalDetails(Base):
    __tablename__ = "rental_details"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id", ondelete="CASCADE"), unique=True)
    price_per_period: Mapped[float] = mapped_column(Float)
    price_period: Mapped[PricePeriod] = mapped_column(SAEnum(PricePeriod))
    deposit_amount: Mapped[float] = mapped_column(Float, default=0.0)
    min_rental_days: Mapped[int] = mapped_column(Integer, default=1)
    max_rental_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    available_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="rental_details")
    rentals: Mapped[List["Rental"]] = relationship("Rental", back_populates="rental_details")


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id"))
    rental_details_id: Mapped[str] = mapped_column(String, ForeignKey("rental_details.id"))
    renter_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    status: Mapped[RentalStatus] = mapped_column(SAEnum(RentalStatus), default=RentalStatus.PENDING)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    total_price: Mapped[float] = mapped_column(Float)
    deposit_amount: Mapped[float] = mapped_column(Float, default=0.0)
    deposit_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    return_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    listing: Mapped["Listing"] = relationship("Listing", back_populates="rentals")
    rental_details: Mapped["RentalDetails"] = relationship("RentalDetails", back_populates="rentals")
    renter: Mapped["User"] = relationship("User", foreign_keys=[renter_id], back_populates="rentals_as_renter")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id], back_populates="rentals_as_owner")
    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="rental", uselist=False)


# ─────────────────────────────────────────────
# SALE / MARKETPLACE
# ─────────────────────────────────────────────

class SaleDetails(Base):
    __tablename__ = "sale_details"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id", ondelete="CASCADE"), unique=True)
    price: Mapped[float] = mapped_column(Float)
    condition: Mapped[ListingCondition] = mapped_column(SAEnum(ListingCondition))
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="sale_details")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="sale_details")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id"))
    sale_details_id: Mapped[str] = mapped_column(String, ForeignKey("sale_details.id"))
    buyer_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    seller_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.PENDING)
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total_amount: Mapped[float] = mapped_column(Float)
    meetup_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    meetup_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    listing: Mapped["Listing"] = relationship("Listing", back_populates="orders")
    sale_details: Mapped["SaleDetails"] = relationship("SaleDetails", back_populates="orders")
    buyer: Mapped["User"] = relationship("User", foreign_keys=[buyer_id], back_populates="orders_as_buyer")
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id], back_populates="orders_as_seller")
    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="order", uselist=False)


# ─────────────────────────────────────────────
# SERVICES
# ─────────────────────────────────────────────

class ServiceDetails(Base):
    __tablename__ = "service_details"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id", ondelete="CASCADE"), unique=True)
    category: Mapped[ServiceCategory] = mapped_column(SAEnum(ServiceCategory))
    price_per_hour: Mapped[float] = mapped_column(Float)
    min_hours: Mapped[int] = mapped_column(Integer, default=1)
    max_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    skill_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    availability: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="service_details")
    bookings: Mapped[List["ServiceBooking"]] = relationship("ServiceBooking", back_populates="service_details")


class ServiceBooking(Base):
    __tablename__ = "service_bookings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id"))
    service_details_id: Mapped[str] = mapped_column(String, ForeignKey("service_details.id"))
    client_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    provider_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus), default=BookingStatus.PENDING)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_hours: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[float] = mapped_column(Float)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    listing: Mapped["Listing"] = relationship("Listing")
    service_details: Mapped["ServiceDetails"] = relationship("ServiceDetails", back_populates="bookings")

    client: Mapped["User"] = relationship(
        "User",
        foreign_keys=[client_id],
        back_populates="service_bookings_as_client",
    )
    provider: Mapped["User"] = relationship(
        "User",
        foreign_keys=[provider_id],
        back_populates="service_bookings_as_provider",
    )

    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="booking", uselist=False)


# ─────────────────────────────────────────────
# MESSAGING
# ─────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("listings.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    participants: Mapped[List["ConversationParticipant"]] = relationship("ConversationParticipant", back_populates="conversation")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="conversations")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")


# ─────────────────────────────────────────────
# REVIEWS, SAVED, REPORTS, NOTIFICATIONS
# ─────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id"))
    reviewer_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    reviewee_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    rental_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("rentals.id"), nullable=True, unique=True)
    order_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("orders.id"), nullable=True, unique=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("service_bookings.id"), nullable=True, unique=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    listing: Mapped["Listing"] = relationship("Listing", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee: Mapped["User"] = relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")
    rental: Mapped[Optional["Rental"]] = relationship("Rental", back_populates="review")
    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="review")
    booking: Mapped[Optional["ServiceBooking"]] = relationship("ServiceBooking", back_populates="review")


class SavedListing(Base):
    __tablename__ = "saved_listings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id", ondelete="CASCADE"))
    saved_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="saved_listings")
    listing: Mapped["Listing"] = relationship("Listing", back_populates="saved_by")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    listing_id: Mapped[str] = mapped_column(String, ForeignKey("listings.id"))
    reported_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    reason: Mapped[ReportReason] = mapped_column(SAEnum(ReportReason))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(SAEnum(ReportStatus), default=ReportStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="reports")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")