import os

import cloudinary

from app.core.config import settings
from app.schemas.health import DependencyStatus


def configure_cloudinary() -> None:
    if settings.cloudinary_url:
        os.environ["CLOUDINARY_URL"] = settings.cloudinary_url
        cloudinary.config(secure=True)
        return

    if not settings.cloudinary_cloud_name:
        return

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def get_cloudinary_status() -> DependencyStatus:
    configured = settings.cloudinary_configured

    return DependencyStatus(
        name="cloudinary",
        ok=True,
        detail="configured" if configured else "not configured; preview uploads disabled",
    )
