from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AddressBase(BaseModel):
    street_address: str
    city: str
    state: str
    pincode: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class AddressRead(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AddressListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    street_address: str
    city: str
    state: str
    pincode: str

