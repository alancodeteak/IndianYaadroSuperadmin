from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.infrastructure.db.models.enums import SubscriptionStatus


class SubscriptionBase(BaseModel):
    shop_id: str
    start_date: datetime
    end_date: datetime
    amount: Decimal
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    last_payment_date: datetime | None = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    amount: Decimal | None = None
    status: SubscriptionStatus | None = None
    last_payment_date: datetime | None = None


class SubscriptionRead(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)

    subscription_id: int
    created_at: datetime
    updated_at: datetime


class SubscriptionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subscription_id: int
    shop_id: str
    amount: Decimal
    status: SubscriptionStatus
    end_date: datetime

