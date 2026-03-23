from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShopOwnerPromotionBase(BaseModel):
    shop_id: str
    promotion_link: str | None = None
    promotion_header: str | None = None
    promotion_content: str | None = None
    promotion_image_s3_key: str | None = None
    is_marketing_enabled: bool = False


class ShopOwnerPromotionCreate(ShopOwnerPromotionBase):
    pass


class ShopOwnerPromotionUpdate(BaseModel):
    promotion_link: str | None = None
    promotion_header: str | None = None
    promotion_content: str | None = None
    promotion_image_s3_key: str | None = None
    is_marketing_enabled: bool | None = None


class ShopOwnerPromotionRead(ShopOwnerPromotionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ShopOwnerPromotionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shop_id: str
    is_marketing_enabled: bool

