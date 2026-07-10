import os
import uuid
from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
BUCKET = "Images"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_product_image(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Uploads image bytes, returns the public URL."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    key = f"{uuid.uuid4().hex}.{ext}"

    supabase.storage.from_(BUCKET).upload(
        key,
        file_bytes,
        {"content-type": content_type or "image/jpeg"},
    )
    return supabase.storage.from_(BUCKET).get_public_url(key)


def delete_product_image(image_url: str) -> None:
    """Deletes an image given its stored public URL. Safe no-op if not found."""
    if not image_url:
        return
    try:
        key = image_url.split(f"/{BUCKET}/")[-1]
        supabase.storage.from_(BUCKET).remove([key])
    except Exception:
        pass  # don't block product ops if cleanup fails