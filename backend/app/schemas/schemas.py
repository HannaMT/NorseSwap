"""
LEARN: Pydantic Schemas (Request & Response Shapes)
=====================================================
This is one of FastAPI's biggest superpowers.

In Node.js/Express, you manually check req.body.email, req.body.password, etc.
In FastAPI, you define the *shape* of data as a class, and FastAPI:
  1. Automatically validates incoming requests
  2. Returns clear error messages for invalid data
  3. Generates your API docs (Swagger UI) automatically
  4. Serializes your response data

Three schema types you'll use:
  - `Base`    → shared fields
  - `Create`  → what the client sends to CREATE something
  - `Response`→ what we send BACK to the client (can hide sensitive fields like password_hash)

`model_config = ConfigDict(from_attributes=True)` tells Pydantic
it can read from SQLAlchemy model instances (not just dicts).
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.models.models import (
    ListingType, ListingStatus, ListingCondition,
    PricePeriod, RentalStatus, OrderStatus,
    BookingStatus, ServiceCategory, NotificationType, ReportReason
)


# ─────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────

class UserRegister(BaseModel):
    """LEARN: This is what the client sends to POST /auth/register"""
    email: EmailStr          # EmailStr automatically validates email format
    password: str
    first_name: str
    last_name: str

    # LEARN: @field_validator lets you add custom validation logic
    # It runs AFTER Pydantic's built-in type checking
    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """What we send back after a successful login"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# ─────────────────────────────────────────────
# USER SCHEMAS
# ─────────────────────────────────────────────

class UserResponse(BaseModel):
    """
    LEARN: This is what we send BACK to the client for a user.
    Notice: no password_hash! We never expose that.
    `from_attributes=True` lets Pydantic read from a SQLAlchemy User object.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    first_name: str
    last_name: str
    university: str
    avatar_url: Optional[str]
    bio: Optional[str]
    is_email_verified: bool
    created_at: datetime


class UserPublicResponse(BaseModel):
    """Minimal user info shown on listings (no email for privacy)"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    university: str
    avatar_url: Optional[str]


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None


# ─────────────────────────────────────────────
# LISTING SCHEMAS
# ─────────────────────────────────────────────

class ListingImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    url: str
    is_primary: bool
    order: int


class RentalDetailsCreate(BaseModel):
    price_per_period: float
    price_period: PricePeriod
    deposit_amount: float = 0.0
    min_rental_days: int = 1
    max_rental_days: Optional[int] = None
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None


class RentalDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    price_per_period: float
    price_period: PricePeriod
    deposit_amount: float
    min_rental_days: int
    max_rental_days: Optional[int]


class SaleDetailsCreate(BaseModel):
    price: float
    condition: ListingCondition
    is_negotiable: bool = False
    quantity: int = 1


class SaleDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    price: float
    condition: ListingCondition
    is_negotiable: bool
    quantity: int


class ServiceDetailsCreate(BaseModel):
    category: ServiceCategory
    price_per_hour: float
    min_hours: int = 1
    max_hours: Optional[int] = None
    skill_level: Optional[str] = None
    availability: Optional[dict] = None


class ServiceDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    category: ServiceCategory
    price_per_hour: float
    min_hours: int
    skill_level: Optional[str]
    availability: Optional[dict]


class ListingCreate(BaseModel):
    """
    LEARN: Union type — `details` can be one of three different schemas.
    FastAPI + Pydantic handle the discrimination automatically.
    """
    type: ListingType
    title: str
    description: str
    category: str
    tags: Optional[List[str]] = []
    location: Optional[str] = None
    allow_other_campuses: bool = False
    rental_details: Optional[RentalDetailsCreate] = None
    sale_details: Optional[SaleDetailsCreate] = None
    service_details: Optional[ServiceDetailsCreate] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    allow_other_campuses: Optional[bool] = None
    status: Optional[ListingStatus] = None


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: ListingType
    status: ListingStatus
    title: str
    description: str
    category: str
    tags: Optional[List[str]]
    university: str
    allow_other_campuses: bool
    location: Optional[str]
    view_count: int
    created_at: datetime
    user: UserPublicResponse
    images: List[ListingImageResponse]
    rental_details: Optional[RentalDetailsResponse]
    sale_details: Optional[SaleDetailsResponse]
    service_details: Optional[ServiceDetailsResponse]
    is_saved: Optional[bool] = False


class ListingListResponse(BaseModel):
    """LEARN: Paginated list response — standard pattern for list endpoints"""
    listings: List[ListingResponse]
    total: int
    page: int
    pages: int
    per_page: int


# ─────────────────────────────────────────────
# RENTAL SCHEMAS
# ─────────────────────────────────────────────

class RentalCreate(BaseModel):
    listing_id: str
    start_date: datetime
    end_date: datetime
    notes: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class RentalRespondRequest(BaseModel):
    action: str  # "approve" or "reject"

    @field_validator("action")
    @classmethod
    def valid_action(cls, v):
        if v not in ("approve", "reject"):
            raise ValueError("Action must be 'approve' or 'reject'")
        return v


class RentalReturnRequest(BaseModel):
    return_notes: Optional[str] = None
    return_deposit: bool = True


class RentalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: RentalStatus
    start_date: datetime
    end_date: datetime
    total_price: float
    deposit_amount: float
    deposit_returned: bool
    notes: Optional[str]
    return_notes: Optional[str]
    created_at: datetime
    listing: "ListingResponse"


# ─────────────────────────────────────────────
# ORDER SCHEMAS
# ─────────────────────────────────────────────

class OrderCreate(BaseModel):
    listing_id: str
    quantity: int = 1
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: OrderStatus
    price: float
    quantity: int
    total_amount: float
    meetup_location: Optional[str]
    meetup_time: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    listing: "ListingResponse"


# ─────────────────────────────────────────────
# SERVICE BOOKING SCHEMAS
# ─────────────────────────────────────────────

class BookingCreate(BaseModel):
    listing_id: str
    scheduled_at: datetime
    duration_hours: int
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: BookingStatus
    scheduled_at: datetime
    duration_hours: int
    total_amount: float
    notes: Optional[str]
    created_at: datetime


# ─────────────────────────────────────────────
# MESSAGING SCHEMAS
# ─────────────────────────────────────────────

class ConversationCreate(BaseModel):
    recipient_id: str
    listing_id: Optional[str] = None


class MessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    is_read: bool
    created_at: datetime
    sender: UserPublicResponse


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    participants: List["ParticipantResponse"]
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user: UserPublicResponse
    last_read_at: Optional[datetime]


# ─────────────────────────────────────────────
# REVIEW SCHEMAS
# ─────────────────────────────────────────────

class ReviewCreate(BaseModel):
    listing_id: str
    reviewee_id: str
    rating: int
    comment: Optional[str] = None
    rental_id: Optional[str] = None
    order_id: Optional[str] = None
    booking_id: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def valid_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    reviewer: UserPublicResponse


class UserReviewsResponse(BaseModel):
    reviews: List[ReviewResponse]
    average_rating: float
    total_reviews: int


# ─────────────────────────────────────────────
# NOTIFICATION SCHEMAS
# ─────────────────────────────────────────────

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: NotificationType
    title: str
    body: str
    data: Optional[dict]
    is_read: bool
    created_at: datetime


# ─────────────────────────────────────────────
# PAYMENT SCHEMAS
# ─────────────────────────────────────────────

class PaymentIntentCreate(BaseModel):
    type: str   # "rental" | "order" | "booking"
    reference_id: str


class PaymentIntentResponse(BaseModel):
    client_secret: str


# ─────────────────────────────────────────────
# REPORT SCHEMAS
# ─────────────────────────────────────────────

class ReportCreate(BaseModel):
    listing_id: str
    reason: ReportReason
    description: Optional[str] = None


# ─────────────────────────────────────────────
# GENERIC RESPONSES
# ─────────────────────────────────────────────

class MessageOnlyResponse(BaseModel):
    """Simple response with just a message string"""
    message: str


class SaveToggleResponse(BaseModel):
    saved: bool