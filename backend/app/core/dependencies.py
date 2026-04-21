"""
LEARN: FastAPI Dependencies
============================
Dependencies are one of FastAPI's killer features.

Instead of manually checking auth in every route (like Express middleware),
you declare what a route DEPENDS on, and FastAPI injects it automatically.

Example — any route that needs an authenticated user:

    @router.get("/my-listings")
    async def get_my_listings(current_user: User = Depends(get_current_user)):
        # current_user is already loaded, verified, and injected here!
        return current_user.listings

This is cleaner than Express middleware because:
  1. It's explicit — you can see exactly what each route requires
  2. It's composable — chain dependencies (e.g., `get_verified_user` calls `get_current_user`)
  3. It's testable — easily mock dependencies in tests
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import User


# LEARN: OAuth2PasswordBearer tells FastAPI to look for a Bearer token
# in the Authorization header: `Authorization: Bearer <token>`
# tokenUrl is used for the Swagger UI "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    LEARN: This dependency:
    1. Extracts the JWT from the Authorization header
    2. Decodes and validates it
    3. Loads the user from DB
    4. Returns the User object to the route handler

    If anything fails, it raises a 401 HTTPException automatically.
    """
    payload = decode_token(token)
    user_id = payload["user_id"]

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
        )
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account banned",
        )
    return user


async def get_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    LEARN: Dependency chaining — this depends on `get_current_user`.
    Any route using `get_verified_user` automatically also gets auth checked.

    Use this for routes that require email verification (posting, renting, etc.)
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your .edu email address to continue.",
        )
    return current_user


async def get_optional_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    LEARN: Optional auth — used on public routes that show extra info if logged in.
    (e.g., showing whether the user has saved a listing)
    Returns None if no token is provided, instead of raising an error.
    """
    if not token:
        return None
    try:
        payload = decode_token(token)
        result = await db.execute(select(User).where(User.id == payload["user_id"]))
        user = result.scalar_one_or_none()
        return user if user and user.is_active and not user.is_banned else None
    except Exception:
        return None