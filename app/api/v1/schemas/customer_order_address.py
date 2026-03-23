from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator


class CustomerOrderAddressBase(BaseModel):
    customer_name: str
    customer_phone_number: int
    address: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    shop_id: str
    credit_balance: Decimal = Decimal("0")
    debit_balance: Decimal = Decimal("0")
    pay_later: bool = False
    is_deleted: bool = False

    @model_validator(mode="after")
    def validate_coordinates_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must both be provided or both be null")
        return self


class CustomerOrderAddressCreate(CustomerOrderAddressBase):
    pass


class CustomerOrderAddressUpdate(BaseModel):
    customer_name: str | None = None
    customer_phone_number: int | None = None
    address: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    credit_balance: Decimal | None = None
    debit_balance: Decimal | None = None
    current_month_order_count: int | None = None
    previous_month_order_count: int | None = None
    current_month_total_amount: Decimal | None = None
    previous_month_total_amount: Decimal | None = None
    current_month_tracked: str | None = None
    previous_month_tracked: str | None = None
    pay_later: bool | None = None
    is_deleted: bool | None = None


class CustomerOrderAddressRead(CustomerOrderAddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_month_order_count: int
    previous_month_order_count: int
    current_month_total_amount: Decimal
    previous_month_total_amount: Decimal
    current_month_tracked: str | None = None
    previous_month_tracked: str | None = None
    created_at: datetime
    updated_at: datetime


class CustomerOrderAddressListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_phone_number: int
    shop_id: str
    pay_later: bool
    is_deleted: bool

