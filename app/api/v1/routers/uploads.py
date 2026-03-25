from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_authenticated
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.uploads import PresignUploadRequest, PresignUploadResponse
from app.domain.enums.roles import Role
from app.infrastructure.storage.s3 import presigned_get_url, presigned_put_url
from app.api.core.config import get_settings


router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/presign", response_model=PresignUploadResponse)
async def presign_upload(
    payload: PresignUploadRequest,
    current_user: CurrentUser = Depends(require_authenticated),
) -> PresignUploadResponse:
    if current_user.role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )

    purpose = payload.purpose.strip()
    if purpose != "shop_owner":
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Unsupported upload purpose",
            status_code=400,
            details={"purpose": purpose},
        )

    s = get_settings()
    prefix = "shop_owners"
    category = (payload.category or "file").strip()
    safe_name = payload.filename.strip().replace("/", "_")
    key = f"{prefix}/{current_user.user_id}/{category}/{uuid4().hex}-{safe_name}"

    upload_url = presigned_put_url(
        purpose="shop_owner",
        key=key,
        content_type=payload.content_type.strip(),
    )
    download_url = presigned_get_url(purpose="shop_owner", key=key)

    return PresignUploadResponse(
        key=key,
        upload_url=upload_url,
        download_url=download_url,
        expires_in=int(s.S3_PRESIGNED_URL_EXPIRY),
    )

