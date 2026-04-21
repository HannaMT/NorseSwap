"""
LEARN: FastAPI Routers
========================
A Router is like an Express Router — it groups related routes.
You create a router, define routes on it, then include it in the main app.

Key FastAPI route concepts:
  - `@router.post("/register")` → HTTP method + path
  - `async def register(...)` → async function (Python equivalent of async/await)
  - Parameters with type hints are automatically parsed:
      - `body: UserRegister` → parse JSON body and validate with Pydantic
      - `db: AsyncSession = Depends(get_db)` → inject DB session
      - `current_user: User = Depends(get_current_user)` → inject auth'd user
  - `status_code=201` → sets the HTTP response code
  - `response_model=UserResponse` → FastAPI will serialize the response using this schema

Compared to Express:
  Express: app.post('/register', async (req, res) => { ... res.json({...}) })
  FastAPI: @router.post("/register") async def register(body: Schema, db = Depends(...)): return data
"""

import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    is_edu_email, get_university_from_email,
)
from app.core.dependencies import get_current_user
from app.models.models import User, EmailVerification, PasswordReset
from app.schemas.schemas import (
    UserRegister, UserLogin, TokenResponse, RefreshRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    UserResponse, MessageOnlyResponse,
)
from app.utils.email import send_verification_email, send_password_reset_email

# LEARN: APIRouter groups all auth endpoints under /auth
# The prefix is applied in main.py when we include this router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageOnlyResponse,
)
async def register(
    body: UserRegister,           # LEARN: FastAPI automatically parses & validates JSON body
    background_tasks: BackgroundTasks,  # LEARN: Run tasks after response is sent (like sending email)
    db: AsyncSession = Depends(get_db), # LEARN: Injected DB session
):
    """
    Register a new user with a .edu email.
    
    LEARN: The docstring appears in the auto-generated Swagger docs at /docs
    """
    # Validate .edu email
    if not is_edu_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must register with an active .edu email address.",
        )

    # Check for existing user
    # LEARN: `select(User).where(...)` is SQLAlchemy's way of:
    #   SELECT * FROM users WHERE email = ?
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    university = get_university_from_email(body.email)

    # LEARN: Create a new User object and add it to the session
    # `db.add(user)` is like staging a change
    # `await db.flush()` sends it to DB but doesn't commit yet
    # The session commits automatically in get_db() after the request
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        university=university,
    )
    db.add(user)
    await db.flush()  # gets the user.id without committing

    # Create email verification token
    token = str(uuid.uuid4())
    verification = EmailVerification(
        user_id=user.id,
        token=token,
        # Naive (Database Compatible)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).replace(tzinfo=None),
    )
    db.add(verification)

    # LEARN: BackgroundTasks sends the email AFTER the response is returned.
    # This means the user gets a fast response and the email sends in the background.
    # It's like setImmediate in Node.js but cleaner.
    background_tasks.add_task(send_verification_email, body.email, body.first_name, token)

    return {"message": "Registration successful! Check your .edu email to verify your account."}


@router.get("/verify-email/{token}", response_model=MessageOnlyResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    LEARN: Path parameters in FastAPI use curly braces: /verify-email/{token}
    FastAPI automatically extracts `token` from the URL and passes it as a function argument.
    """
    result = await db.execute(
        select(EmailVerification).where(EmailVerification.token == token)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")

    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await db.delete(record)
        raise HTTPException(status_code=400, detail="Link expired. Please request a new one.")

    # Update user + delete verification record
    result = await db.execute(select(User).where(User.id == record.user_id))
    user = result.scalar_one()
    user.is_email_verified = True
    await db.delete(record)

    return {"message": "Email verified! You can now log in."}


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # LEARN: Always use the same error for wrong email or wrong password.
    # Never say "email not found" — that's an info leak (enumeration attack).
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if user.is_banned:
        raise HTTPException(status_code=403, detail="Your account has been banned.")

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your .edu email before logging in.",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token, expected_type="refresh")
    result = await db.execute(select(User).where(User.id == payload["user_id"]))
    user = result.scalar_one_or_none()

    if not user or not user.is_active or user.is_banned:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    return {"access_token": create_access_token(user.id)}


@router.post("/forgot-password", response_model=MessageOnlyResponse)
async def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Always return the same message to prevent email enumeration
    if user:
        token = str(uuid.uuid4())
        reset = PasswordReset(
            user_id=user.id,
            token=token,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
        )
        db.add(reset)
        background_tasks.add_task(send_password_reset_email, user.email, user.first_name, token)

    return {"message": "If that email exists, a reset link was sent."}


@router.post("/reset-password", response_model=MessageOnlyResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordReset).where(PasswordReset.token == body.token)
    )
    record = result.scalar_one_or_none()

    if not record or record.used_at or record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    result = await db.execute(select(User).where(User.id == record.user_id))
    user = result.scalar_one()
    user.password_hash = hash_password(body.new_password)
    record.used_at = datetime.now(timezone.utc)

    return {"message": "Password reset successfully. Please log in."}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),  # LEARN: Injected from JWT automatically
):
    """Get the currently authenticated user."""
    return current_user


@router.post("/resend-verification", response_model=MessageOnlyResponse)
async def resend_verification(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user and not user.is_email_verified:
        # Delete existing verification
        await db.execute(
            delete(EmailVerification).where(EmailVerification.user_id == user.id)
        )
        token = str(uuid.uuid4())
        db.add(EmailVerification(
            user_id=user.id,
            token=token,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),

        ))
        background_tasks.add_task(send_verification_email, user.email, user.first_name, token)

    return {"message": "If that email is registered and unverified, we sent a new link."}