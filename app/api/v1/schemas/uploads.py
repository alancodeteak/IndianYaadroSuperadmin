from __future__ import annotations

from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    # "shop_owner" is used for shop owner photo / promotion images
    purpose: str = Field(default="shop_owner", max_length=50)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    # Optional hint to group uploads (e.g. "photo" / "promotion")
    category: str | None = Field(default=None, max_length=50)


class PresignUploadResponse(BaseModel):
    key: str
    upload_url: str
    download_url: str
    expires_in: int
