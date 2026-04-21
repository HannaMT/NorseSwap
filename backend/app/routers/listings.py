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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_verified_user, get_optional_user

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from app.models.models import (
    Listing, ListingImage, RentalDetails, SaleDetails, ServiceDetails,
    SavedListing, User, ListingType, ListingStatus, PricePeriod, ListingCondition, ServiceCategory
)
from app.schemas.schemas import (
    ListingUpdate, ListingResponse, ListingListResponse,
    MessageOnlyResponse, SaveToggleResponse
)
from app.utils.cloudinary import upload_images, delete_image

router = APIRouter(prefix="/listings", tags=["Listings"])

LISTINGS_PER_PAGE = 20


def _normalize_optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


async def _get_listing_for_response(db: AsyncSession, listing_id: str) -> Listing:
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
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return listing


async def _get_owned_listing_or_404(db: AsyncSession, listing_id: str, user_id: str) -> Listing:
    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.images))
        .where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    if listing.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this listing.")
    if listing.status == ListingStatus.DELETED:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return listing


@router.get("", response_model=ListingListResponse)
async def get_listings(
    type: Optional[ListingType] = Query(None),
    category: Optional[str] = Query(None),
    university: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    sort_by: str = Query("newest"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
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
        .where(Listing.status == ListingStatus.ACTIVE)
    )
    if current_user:
        query = query.where(Listing.user_id != current_user.id)

    if type:
        query = query.where(Listing.type == type)
    if category:
        query = query.where(Listing.category == category)

    target_uni = university or (current_user.university if current_user else None)
    if target_uni:
        query = query.where(
            or_(Listing.university == target_uni, Listing.allow_other_campuses == True)
        )

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Listing.title.ilike(search_term),
                Listing.description.ilike(search_term),
            )
        )

    if sort_by == "newest":
        query = query.order_by(Listing.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Listing.created_at.asc())
    elif sort_by == "popular":
        query = query.order_by(Listing.view_count.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    offset = (page - 1) * LISTINGS_PER_PAGE
    query = query.offset(offset).limit(LISTINGS_PER_PAGE)

    result = await db.execute(query)
    listings = result.scalars().all()

    saved_ids = set()
    if current_user:
        saved_result = await db.execute(
            select(SavedListing.listing_id).where(SavedListing.user_id == current_user.id)
        )
        saved_ids = {row[0] for row in saved_result.fetchall()}

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
    listing = await _get_listing_for_response(db, listing_id)

    if listing.status == ListingStatus.DELETED:
        raise HTTPException(status_code=404, detail="Listing not found.")

    await db.execute(
        update(Listing).where(Listing.id == listing_id).values(view_count=Listing.view_count + 1)
    )

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
    title: str = Form(...),
    description: str = Form(...),
    type: ListingType = Form(...),
    category: str = Form(...),
    location: Optional[str] = Form(None),
    allow_other_campuses: bool = Form(False),
    tags: Optional[str] = Form(None),
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
    images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    uploaded_images = []
    if images:
        try:
            uploaded_images = await upload_images(images, current_user.university)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Image upload failed: {str(exc)}")

    listing = Listing(
        user_id=current_user.id,
        type=type,
        title=title.strip(),
        description=description.strip(),
        category=category.strip(),
        tags=[t.strip() for t in tags.split(",") if t.strip()] if tags else [],
        university=current_user.university,
        allow_other_campuses=allow_other_campuses,
        location=_normalize_optional_str(location),
    )
    db.add(listing)
    await db.flush()

    for idx, img in enumerate(uploaded_images):
        db.add(
            ListingImage(
                listing_id=listing.id,
                url=img["url"],
                public_id=img["public_id"],
                is_primary=idx == 0,
                order=idx,
            )
        )

    if type == ListingType.RENTAL:
        if rental_price_per_period is None or not rental_price_period:
            raise HTTPException(
                status_code=400,
                detail="Rental listings require rental_price_per_period and rental_price_period.",
            )
        try:
            price_period = PricePeriod(rental_price_period)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rental_price_period: {rental_price_period}",
            )

        db.add(
            RentalDetails(
                listing_id=listing.id,
                price_per_period=rental_price_per_period,
                price_period=price_period,
                deposit_amount=rental_deposit or 0,
                min_rental_days=rental_min_days or 1,
            )
        )

    elif type == ListingType.SALE:
        if sale_price is None or not sale_condition:
            raise HTTPException(
                status_code=400,
                detail="Sale listings require sale_price and sale_condition.",
            )
        try:
            condition = ListingCondition(sale_condition)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sale_condition: {sale_condition}",
            )

        db.add(
            SaleDetails(
                listing_id=listing.id,
                price=sale_price,
                condition=condition,
                is_negotiable=sale_is_negotiable or False,
                quantity=sale_quantity or 1,
            )
        )

    elif type == ListingType.SERVICE:
        if service_price_per_hour is None or not service_category:
            raise HTTPException(
                status_code=400,
                detail="Service listings require service_category and service_price_per_hour.",
            )
        try:
            service_cat = ServiceCategory(service_category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service_category: {service_category}",
            )

        db.add(
            ServiceDetails(
                listing_id=listing.id,
                category=service_cat,
                price_per_hour=service_price_per_hour,
                skill_level=_normalize_optional_str(service_skill_level),
            )
        )

    await db.flush()
    return await _get_listing_for_response(db, listing.id)


@router.post("/{listing_id}/images", response_model=ListingResponse)
async def add_listing_images(
    listing_id: str,
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned_listing_or_404(db, listing_id, current_user.id)

    if not images:
        raise HTTPException(status_code=400, detail="Please choose at least one image.")

    existing_count = len(listing.images)
    if existing_count + len(images) > 8:
        raise HTTPException(status_code=400, detail="A listing can have at most 8 images.")

    try:
        uploaded_images = await upload_images(images, current_user.university)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image upload failed: {str(exc)}")

    for offset, img in enumerate(uploaded_images):
        db.add(
            ListingImage(
                listing_id=listing.id,
                url=img["url"],
                public_id=img["public_id"],
                is_primary=(existing_count == 0 and offset == 0),
                order=existing_count + offset,
            )
        )

    await db.flush()
    return await _get_listing_for_response(db, listing.id)


@router.delete("/{listing_id}/images/{image_id}", response_model=ListingResponse)
async def delete_listing_image(
    listing_id: str,
    image_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned_listing_or_404(db, listing_id, current_user.id)

    target = next((img for img in listing.images if img.id == image_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Image not found.")

    if len(listing.images) == 1:
        raise HTTPException(status_code=400, detail="A listing must keep at least one image.")

    deleted_was_primary = target.is_primary
    deleted_order = target.order
    public_id = target.public_id

    await db.delete(target)

    remaining_images = [img for img in listing.images if img.id != image_id]
    remaining_images.sort(key=lambda img: img.order)

    for idx, image in enumerate(remaining_images):
        image.order = idx
        if deleted_was_primary:
            image.is_primary = idx == 0
        elif image.id != image_id:
            if image.order >= deleted_order:
                image.order = max(0, idx)

    await db.flush()

    if public_id:
        await delete_image(public_id)

    return await _get_listing_for_response(db, listing.id)


@router.patch("/{listing_id}/images/{image_id}/primary", response_model=ListingResponse)
async def set_primary_listing_image(
    listing_id: str,
    image_id: str,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned_listing_or_404(db, listing_id, current_user.id)

    target = next((img for img in listing.images if img.id == image_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Image not found.")

    for image in listing.images:
        image.is_primary = image.id == image_id

    ordered = sorted(listing.images, key=lambda img: (img.id != image_id, img.order))
    for idx, image in enumerate(ordered):
        image.order = idx

    await db.flush()
    return await _get_listing_for_response(db, listing.id)


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

    listing.status = ListingStatus.DELETED
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
