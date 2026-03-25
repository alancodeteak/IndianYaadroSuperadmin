from __future__ import annotations

from functools import lru_cache
from typing import Literal

from app.api.core.config import get_settings


BucketPurpose = Literal["shop_owner", "delivery_partner", "orders", "tickets"]

def _require_boto3():
    try:
        import boto3  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "boto3 is required for S3 features. Install dependencies (pip install -r requirements.txt)."
        ) from exc
    return boto3


@lru_cache
def _client():
    s = get_settings()
    boto3 = _require_boto3()
    # If keys are empty, boto3 can still fall back to env/instance roles.
    kwargs = {"region_name": s.AWS_REGION or None}
    if s.AWS_ACCESS_KEY_ID and s.AWS_SECRET_ACCESS_KEY:
        kwargs.update(
            aws_access_key_id=s.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=s.AWS_SECRET_ACCESS_KEY,
        )
    return boto3.client("s3", **kwargs)


def _bucket_for(purpose: BucketPurpose) -> str:
    s = get_settings()
    mapping = {
        "shop_owner": s.PROD_S3_BUCKET_SHOP_OWNER,
        "delivery_partner": s.PROD_S3_BUCKET_DELIVERY_PARTNER,
        "orders": s.PROD_S3_BUCKET_ORDERS,
        "tickets": s.PROD_S3_BUCKET_TICKETS,
    }
    return mapping[purpose]


def is_http_url(value: str) -> bool:
    v = value.lower()
    return v.startswith("http://") or v.startswith("https://")


def presigned_get_url(*, purpose: BucketPurpose, key: str) -> str:
    s = get_settings()
    bucket = _bucket_for(purpose)
    return _client().generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=int(s.S3_PRESIGNED_URL_EXPIRY),
    )


def presigned_put_url(*, purpose: BucketPurpose, key: str, content_type: str) -> str:
    s = get_settings()
    bucket = _bucket_for(purpose)
    return _client().generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
            **({"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": s.AWS_S3_KMS_KEY_ID}
               if s.AWS_S3_KMS_KEY_ID else {}),
        },
        ExpiresIn=int(s.S3_PRESIGNED_URL_EXPIRY),
    )


def put_object(
    *,
    purpose: BucketPurpose,
    key: str,
    body: bytes,
    content_type: str,
) -> None:
    s = get_settings()
    bucket = _bucket_for(purpose)
    extra = {"ContentType": content_type}
    if s.AWS_S3_KMS_KEY_ID:
        extra.update(
            {
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": s.AWS_S3_KMS_KEY_ID,
            }
        )
    _client().put_object(Bucket=bucket, Key=key, Body=body, **extra)
