from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StandardMeta(BaseModel):
    """
    Placeholder for pagination/other meta.
    Keep optional to support endpoints that don't need it.
    """

    page: Optional[int] = None
    pageSize: Optional[int] = None


class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: Optional[StandardMeta] = None


class ErrorItem(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorItem

