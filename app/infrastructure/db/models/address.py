from decimal import Decimal

from sqlalchemy import Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.mixins import TimestampMixin


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_pincode", "pincode"),
        Index("ix_addresses_city_state", "city", "state"),
        Index("ix_addresses_latitude_longitude", "latitude", "longitude"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    street_address: Mapped[str] = mapped_column(String(250), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)

    shop_owners = relationship("ShopOwner", back_populates="address")

