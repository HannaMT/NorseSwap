"""
LEARN: Security Utilities
==========================
This module handles:
1. Password hashing (bcrypt)
2. JWT token creation & verification
3. .edu email validation
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import re
import bcrypt

from jose import JWTError, jwt  # type: ignore[import-untyped]
from fastapi import HTTPException, status

from app.core.config import settings

# ─── Password Utilities ───────────────────────

def hash_password(password: str) -> str:
    """Modern replacement for passlib's hash function"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against a bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    if not hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        return False  
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ─── JWT Token Utilities ──────────────────────

def create_access_token(user_id: str) -> str:
    """
    Creates a JWT access token. 
    Added .replace(tzinfo=None) to prevent SQLAlchemy TIMESTAMP WITHOUT TIME ZONE errors.
    """
    # Calculate expiry with UTC awareness, then strip it for DB/Library compatibility
    expire = (datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )).replace(tzinfo=None)
    
    payload = {
        "sub": user_id,
        "exp": expire,            
        "type": "access",
        "jti": str(uuid.uuid4()), 
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Creates a JWT refresh token.
    Added .replace(tzinfo=None) to prevent SQLAlchemy TIMESTAMP WITHOUT TIME ZONE errors.
    """
    expire = (datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )).replace(tzinfo=None)
    
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Decode and verify a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")

        if user_id is None or token_type != expected_type:
            raise credentials_exception

        return {"user_id": user_id}
    except JWTError:
        raise credentials_exception

# ... (rest of the email validation functions remain unchanged)


# ─── .edu Email Validation ────────────────────

# Known non-student .edu domains to block
BLOCKED_EDU_DOMAINS = {"k12.edu", "email.edu"}

# 50+ major university domain mappings
UNIVERSITY_MAP = {
    "mit.edu": "MIT",
    "harvard.edu": "Harvard University",
    "stanford.edu": "Stanford University",
    "yale.edu": "Yale University",
    "princeton.edu": "Princeton University",
    "columbia.edu": "Columbia University",
    "uchicago.edu": "University of Chicago",
    "upenn.edu": "University of Pennsylvania",
    "dartmouth.edu": "Dartmouth College",
    "cornell.edu": "Cornell University",
    "brown.edu": "Brown University",
    "gatech.edu": "Georgia Tech",
    "umich.edu": "University of Michigan",
    "berkeley.edu": "UC Berkeley",
    "ucla.edu": "UCLA",
    "usc.edu": "USC",
    "nyu.edu": "NYU",
    "bu.edu": "Boston University",
    "northeastern.edu": "Northeastern University",
    "tufts.edu": "Tufts University",
    "bc.edu": "Boston College",
    "nd.edu": "Notre Dame",
    "georgetown.edu": "Georgetown University",
    "duke.edu": "Duke University",
    "unc.edu": "UNC Chapel Hill",
    "vanderbilt.edu": "Vanderbilt University",
    "emory.edu": "Emory University",
    "rice.edu": "Rice University",
    "tulane.edu": "Tulane University",
    "utexas.edu": "UT Austin",
    "uw.edu": "University of Washington",
    "purdue.edu": "Purdue University",
    "illinois.edu": "UIUC",
    "wisc.edu": "UW-Madison",
    "msu.edu": "Michigan State University",
    "psu.edu": "Penn State",
    "rutgers.edu": "Rutgers University",
    "fsu.edu": "Florida State University",
    "ufl.edu": "University of Florida",
    "miami.edu": "University of Miami",
    "colorado.edu": "CU Boulder",
    "arizona.edu": "University of Arizona",
    "asu.edu": "Arizona State University",
    "nku.edu": "Northern Kentucky University",
}


def is_edu_email(email: str) -> bool:
    """Return True only if the email is a valid .edu address"""
    if not email:
        return False
    email = email.lower().strip()
    # Must end in .edu
    if not re.match(r"^[^\s@]+@[^\s@]+\.edu$", email):
        return False
    domain = email.split("@")[1]
    # Block known non-student domains
    for blocked in BLOCKED_EDU_DOMAINS:
        if domain.endswith(blocked):
            return False
    return True


def get_university_from_email(email: str) -> str:
    """
    Extract university name from an .edu email domain.
    e.g. jsmith@mit.edu → "MIT"
    e.g. jsmith@students.gatech.edu → "Georgia Tech"
    """
    domain = email.lower().split("@")[1]

    # Direct match
    if domain in UNIVERSITY_MAP:
        return UNIVERSITY_MAP[domain]

    # Subdomain match (e.g., students.gatech.edu → gatech.edu)
    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        sub = ".".join(parts[i:])
        if sub in UNIVERSITY_MAP:
            return UNIVERSITY_MAP[sub]

    # Fallback: prettify domain name
    base = parts[-2]
    return base.capitalize() + " University"