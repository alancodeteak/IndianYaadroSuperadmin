from __future__ import annotations
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import CurrentUser, require_authenticated
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.uploads import PresignUploadRequest, PresignUploadResponse
from app.domain.enums.roles import Role
from app.infrastructure.storage.s3 import presigned_get_url, presigned_put_url, put_object
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

    try:
        upload_url = presigned_put_url(
            purpose="shop_owner",
            key=key,
            content_type=payload.content_type.strip(),
        )
        download_url = presigned_get_url(purpose="shop_owner", key=key)
    except RuntimeError as exc:
        raise ApiError(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="S3 upload is not configured on this server (missing dependency). Install boto3.",
            status_code=503,
        ) from exc

    return PresignUploadResponse(
        key=key,
        upload_url=upload_url,
        download_url=download_url,
        expires_in=int(s.S3_PRESIGNED_URL_EXPIRY),
    )


@router.post("/shop-owner/photo", response_model=PresignUploadResponse)
async def upload_shop_owner_photo_via_backend(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    category: str = Form("photo"),
    current_user: CurrentUser = Depends(require_authenticated),
) -> PresignUploadResponse:
    """
    Backend-proxy upload (browser -> FastAPI -> S3).
    Use this when S3 bucket CORS isn't configured for direct browser uploads.
    """
    if current_user.role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )

    s = get_settings()
    if not file.content_type or not file.filename:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid upload",
            status_code=400,
        )

    content_type = file.content_type.strip()
    safe_name = file.filename.strip().replace("/", "_")
    key = f"shop_owners/{user_id}/{category.strip()}/{uuid4().hex}-{safe_name}"

    data = await file.read()
    if len(data) > int(s.S3_MAX_FILE_SIZE):
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="File too large",
            status_code=400,
            details={"max_bytes": int(s.S3_MAX_FILE_SIZE)},
        )

    try:
        put_object(purpose="shop_owner", key=key, body=data, content_type=content_type)
        download_url = presigned_get_url(purpose="shop_owner", key=key)
        upload_url = presigned_put_url(
            purpose="shop_owner", key=key, content_type=content_type
        )
    except RuntimeError as exc:
        raise ApiError(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="S3 upload is not configured on this server (missing dependency). Install boto3.",
            status_code=503,
        ) from exc

    return PresignUploadResponse(
        key=key,
        upload_url=upload_url,
        download_url=download_url,
        expires_in=int(s.S3_PRESIGNED_URL_EXPIRY),
    )

