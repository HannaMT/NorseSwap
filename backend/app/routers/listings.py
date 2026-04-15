"""
LEARN: Listings Router
========================
This shows more advanced FastAPI patterns:
  - Query parameters (URL filters like ?type=RENTAL&page=2)
  - File uploads (images to Cloudinary)
  - Pagination pattern
  - Optional auth (public route but shows extra info if logged in)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_verified_user, get_optional_user
from app.models.models import (
    Listing, ListingImage, RentalDetails, SaleDetails, ServiceDetails,
    SavedListing, User, ListingType, ListingStatus
)
from app.schemas.schemas import (
    ListingCreate, ListingUpdate, ListingResponse, ListingListResponse,
    MessageOnlyResponse, SaveToggleResponse
)
from app.utils.cloudinary import upload_images

router = APIRouter(prefix="/listings", tags=["Listings"])

LISTINGS_PER_PAGE = 20


@router.get("", response_model=ListingListResponse)
async def get_listings(
    # LEARN: Query parameters are declared as function arguments with defaults.
    # GET /listings?type=RENTAL&category=Bikes&page=2&search=trek
    type: Optional[ListingType] = Query(None),
    category: Optional[str] = Query(None),
    university: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    page: int = Query(1, ge=1),               # ge=1 means "greater than or equal to 1"
    sort_by: str = Query("newest"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    # Build the query dynamically based on filters
    # LEARN: SQLAlchemy lets you build queries step by step
    query = (
        select(Listing)
        .options(
            selectinload(Listing.user),        # LEARN: Eagerly load related user
            selectinload(Listing.images),      # Eagerly load images
            selectinload(Listing.rental_details),
            selectinload(Listing.sale_details),
            selectinload(Listing.service_details),
        )
        .where(Listing.status == ListingStatus.ACTIVE)
    )

    # Filter by type
    if type:
        query = query.where(Listing.type == type)

    # Filter by category
    if category:
        query = query.where(Listing.category == category)

    # University scoping — only show same campus unless cross-campus enabled
    target_uni = university or (current_user.university if current_user else None)
    if target_uni:
        query = query.where(
            or_(Listing.university == target_uni, Listing.allow_other_campuses == True)
        )

    # Full-text search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Listing.title.ilike(search_term),       # case-insensitive LIKE
                Listing.description.ilike(search_term),
            )
        )

    # Sorting
    if sort_by == "newest":
        query = query.order_by(Listing.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Listing.created_at.asc())
    elif sort_by == "popular":
        query = query.order_by(Listing.view_count.desc())

    # Count total (for pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Apply pagination
    offset = (page - 1) * LISTINGS_PER_PAGE
    query = query.offset(offset).limit(LISTINGS_PER_PAGE)

    result = await db.execute(query)
    listings = result.scalars().all()

    # Get saved listing IDs for the current user
    saved_ids = set()
    if current_user:
        saved_result = await db.execute(
            select(SavedListing.listing_id).where(SavedListing.user_id == current_user.id)
        )
        saved_ids = {row[0] for row in saved_result.fetchall()}

    # Build response with is_saved field
    listing_responses = []
    for listing in listings:
        data = ListingResponse.model_validate(listing)
        data.is_saved = listing.id in saved_ids
        listing_responses.append(data)

    return ListingListResponse(
        listings=listing_responses,
        total=total,
        page=page,
        pages=(total + LISTINGS_PER_PAGE - 1) // LISTINGS_PER_PAGE,
        per_page=LISTINGS_PER_PAGE,
    )


@router.get("/me", response_model=List[ListingResponse])
async def get_my_listings(
    type: Optional[ListingType] = Query(None),
    status: Optional[ListingStatus] = Query(None),
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Listing)
        .options(
            selectinload(Listing.user),
            selectinload(Listing.images),
            selectinload(Listing.rental_details),
            selectinload(Listing.sale_details),
            selectinload(Listing.service_details),
        )
        .where(Listing.user_id == current_user.id)
        .where(Listing.status != ListingStatus.DELETED)
        .order_by(Listing.created_at.desc())
    )
    if type:
        query = query.where(Listing.type == type)
    if status:
        query = query.where(Listing.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    result = await db.execute(
        select(Listing)
        .options(
            selectinload(Listing.user),
            selectinload(Listing.images),
            selectinload(Listing.rental_details),
            selectinload(Listing.sale_details),
            selectinload(Listing.service_details),
        )
        .where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()

    if not listing or listing.status == ListingStatus.DELETED:
        raise HTTPException(status_code=404, detail="Listing not found.")

    # Increment view count (fire-and-forget style)
    await db.execute(
        update(Listing).where(Listing.id == listing_id).values(view_count=Listing.view_count + 1)
    )

    # Check if saved
    is_saved = False
    if current_user:
        saved = await db.execute(
            select(SavedListing).where(
                SavedListing.user_id == current_user.id,
                SavedListing.listing_id == listing_id,
            )
        )
        is_saved = saved.scalar_one_or_none() is not None

    response = ListingResponse.model_validate(listing)
    response.is_saved = is_saved
    return response


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ListingResponse)
async def create_listing(
    # LEARN: Mixing JSON body + file uploads requires Form data
    # We use Form() fields alongside File() uploads
    title: str = Form(...),                            # ... means required
    description: str = Form(...),
    type: ListingType = Form(...),
    category: str = Form(...),
    location: Optional[str] = Form(None),
    allow_other_campuses: bool = Form(False),
    tags: Optional[str] = Form(None),                 # comma-separated string
    rental_price_per_period: Optional[float] = Form(None),
    rental_price_period: Optional[str] = Form(None),
    rental_deposit: Optional[float] = Form(0),
    rental_min_days: Optional[int] = Form(1),
    sale_price: Optional[float] = Form(None),
    sale_condition: Optional[str] = Form(None),
    sale_is_negotiable: Optional[bool] = Form(False),
    sale_quantity: Optional[int] = Form(1),
    service_category: Optional[str] = Form(None),
    service_price_per_hour: Optional[float] = Form(None),
    service_skill_level: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),       # 0 to 8 images
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Upload images to Cloudinary
    uploaded_images = []
    if images:
        uploaded_images = await upload_images(images, current_user.university)

    # Create the listing
    listing = Listing(
        user_id=current_user.id,
        type=type,
        title=title,
        description=description,
        category=category,
        tags=[t.strip() for t in tags.split(",")] if tags else [],
        university=current_user.university,
        allow_other_campuses=allow_other_campuses,
        location=location,
    )
    db.add(listing)
    await db.flush()

    # Add images
    for idx, img in enumerate(uploaded_images):
        db.add(ListingImage(
            listing_id=listing.id,
            url=img["url"],
            public_id=img["public_id"],
            is_primary=idx == 0,
            order=idx,
        ))

    # Add type-specific details
    if type == ListingType.RENTAL and rental_price_per_period:
        db.add(RentalDetails(
            listing_id=listing.id,
            price_per_period=rental_price_per_period,
            price_period=rental_price_period,
            deposit_amount=rental_deposit or 0,
            min_rental_days=rental_min_days or 1,
        ))
    elif type == ListingType.SALE and sale_price:
        db.add(SaleDetails(
            listing_id=listing.id,
            price=sale_price,
            condition=sale_condition,
            is_negotiable=sale_is_negotiable or False,
            quantity=sale_quantity or 1,
        ))
    elif type == ListingType.SERVICE and service_price_per_hour:
        db.add(ServiceDetails(
            listing_id=listing.id,
            category=service_category,
            price_per_hour=service_price_per_hour,
            skill_level=service_skill_level,
        ))

    await db.flush()

    # Reload with relationships for response
    result = await db.execute(
        select(Listing)
        .options(
            selectinload(Listing.user),
            selectinload(Listing.images),
            selectinload(Listing.rental_details),
            selectinload(Listing.sale_details),
            selectinload(Listing.service_details),
        )
        .where(Listing.id == listing.id)
    )
    return result.scalar_one()


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    body: ListingUpdate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    if listing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own this listing.")

    # LEARN: `model_dump(exclude_unset=True)` returns only the fields
    # that were actually provided in the request body (not defaults).
    # This lets us do partial updates without overwriting existing data.
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)

    await db.flush()
    return listing


@router.delete("/{listing_id}", response_model=MessageOnlyResponse)
async def delete_listing(
    listing_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    if listing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own this listing.")

    listing.status = ListingStatus.DELETED  # Soft delete
    return {"message": "Listing deleted."}


@router.post("/{listing_id}/save", response_model=SaveToggleResponse)
async def toggle_save(
    listing_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedListing).where(
            SavedListing.user_id == current_user.id,
            SavedListing.listing_id == listing_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        return {"saved": False}
    else:
        db.add(SavedListing(user_id=current_user.id, listing_id=listing_id))
        return {"saved": True}