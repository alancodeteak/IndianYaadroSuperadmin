from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.mixins import TimestampMixin


class ShopOwnerPromotion(Base, TimestampMixin):
    __tablename__ = "shopowner_promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(
        ForeignKey("shop_owners.shop_id"), unique=True, nullable=False
    )
    promotion_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    promotion_header: Mapped[str | None] = mapped_column(String(255), nullable=True)
    promotion_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    promotion_image_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_marketing_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shop_owner = relationship("ShopOwner", back_populates="promotion")

