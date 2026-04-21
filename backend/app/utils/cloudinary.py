"""
LEARN: Cloudinary Image Uploads
=================================
Cloudinary handles all our image storage and transformation.
When a user uploads a listing photo:
  1. We receive the file via FastAPI (UploadFile)
  2. Read its bytes into memory
  3. Upload to Cloudinary asynchronously
  4. Cloudinary returns a URL + public_id
  5. We store those in the DB (ListingImage table)

Why Cloudinary over storing files locally?
  - Local files are wiped on server restart/redeploy
  - Cloudinary auto-resizes, compresses, and CDN-serves images
  - Built-in transformations (crop, quality, format conversion)

LEARN: The sync issue
  cloudinary.uploader.upload() is SYNCHRONOUS — it blocks the event loop.
  We fix this by running it in a thread pool executor using asyncio.
  This is the standard Python pattern for running sync code inside async functions.
"""

import asyncio
from functools import partial
from typing import List, Optional

import cloudinary  # type: ignore[import-untyped]
import cloudinary.uploader  # type: ignore[import-untyped]
from fastapi import UploadFile, HTTPException

from app.core.config import settings

# Configure Cloudinary once at module load time
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,  # Always use HTTPS URLs
)

# Allowed image MIME types
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per image
MAX_IMAGES = 8                     # Max images per listing


async def _upload_to_cloudinary(contents: bytes, folder: str, **kwargs) -> dict:
    """
    LEARN: Running sync code in async context.

    cloudinary.uploader.upload() is blocking (sync).
    Calling it directly inside an async function would freeze
    the entire server until the upload finishes.

    The fix: `asyncio.get_event_loop().run_in_executor(None, fn)`
    This runs the sync function in a separate thread, freeing the
    event loop to handle other requests while we wait for Cloudinary.

    `partial()` is used to pre-fill the function arguments so we
    can pass it as a zero-argument callable to run_in_executor.
    """
    loop = asyncio.get_event_loop()
    upload_fn = partial(
        cloudinary.uploader.upload,
        contents,
        folder=folder,
        **kwargs,
    )
    return await loop.run_in_executor(None, upload_fn)


async def upload_images(files: List[UploadFile], university: str) -> List[dict]:
    """
    Upload a list of images to Cloudinary.
    Returns a list of dicts with 'url' and 'public_id' for each image.

    Images are stored in a university-specific folder:
      campusloop/MIT/abc123.jpg
    """
    if not files:
        return []

    folder = f"campusloop/{university.replace(' ', '_').lower()}"
    results = []

    for file in files[:MAX_IMAGES]:
        # Validate file type
        content_type = file.content_type or ""
        if content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{content_type}' is not allowed. Use JPEG, PNG, WebP, or GIF.",
            )

        # Read and validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' is too large. Maximum size is 10MB.",
            )
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail=f"'{file.filename}' is empty.")

        # Upload to Cloudinary with auto-optimization
        result = await _upload_to_cloudinary(
            contents,
            folder=folder,
            transformation=[
                {
                    "width": 1200,
                    "height": 900,
                    "crop": "limit",       # Never upscale, only shrink
                    "quality": "auto",     # Cloudinary picks best quality/size balance
                    "fetch_format": "auto", # Serve WebP to browsers that support it
                }
            ],
            resource_type="image",
        )

        results.append({
            "url": result["secure_url"],
            "public_id": result["public_id"],
        })

    return results


async def upload_avatar(file: UploadFile, user_id: str) -> dict:
    """
    Upload a single profile picture.
    Applies a square crop and smaller dimensions for avatars.
    Stored at: campusloop/avatars/{user_id}
    """
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Avatar must be a JPEG, PNG, or WebP image.",
        )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB limit for avatars
        raise HTTPException(status_code=400, detail="Avatar must be under 5MB.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Avatar file is empty.")

    result = await _upload_to_cloudinary(
        contents,
        folder="campusloop/avatars",
        public_id=user_id,          # Use user_id as filename → overwrites old avatar
        overwrite=True,
        transformation=[
            {
                "width": 400,
                "height": 400,
                "crop": "fill",         # Square crop, centered on face
                "gravity": "face",      # Smart face detection for cropping
                "quality": "auto",
                "fetch_format": "auto",
            }
        ],
    )

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
    }


async def delete_image(public_id: str) -> bool:
    """
    Delete an image from Cloudinary by its public_id.
    Called when a listing is deleted or an image is removed.
    Returns True if deletion succeeded.
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(cloudinary.uploader.destroy, public_id, resource_type="image"),
        )
        return result.get("result") == "ok"
    except Exception:
        # Don't crash the app if Cloudinary deletion fails
        # The image will just be orphaned in Cloudinary (not a critical error)
        return False


async def delete_images(public_ids: List[str]) -> None:
    """Delete multiple images from Cloudinary in parallel."""
    if not public_ids:
        return
    # Run all deletions concurrently
    await asyncio.gather(*[delete_image(pid) for pid in public_ids])


def get_thumbnail_url(url: str, width: int = 400, height: int = 300) -> Optional[str]:
    """
    LEARN: Cloudinary URL transformation.

    Cloudinary lets you transform images just by modifying the URL.
    This takes a full-size image URL and returns a thumbnail URL.

    Original:  https://res.cloudinary.com/demo/image/upload/sample.jpg
    Thumbnail: https://res.cloudinary.com/demo/image/upload/w_400,h_300,c_fill/sample.jpg

    No extra API call needed — Cloudinary generates the thumbnail on-the-fly
    and caches it on their CDN.
    """
    if not url or "cloudinary.com" not in url:
        return url

    # Insert transformation parameters into the Cloudinary URL
    parts = url.split("/upload/")
    if len(parts) != 2:
        return url

    transform = f"w_{width},h_{height},c_fill,q_auto,f_auto"
    return f"{parts[0]}/upload/{transform}/{parts[1]}"