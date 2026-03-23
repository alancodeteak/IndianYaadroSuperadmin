import enum


class ShopStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class ShopPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class DeliveryPartnerStatus(str, enum.Enum):
    IDLE = "idle"
    ORDER_ASSIGNED = "order_assigned"
    ONGOING = "ongoing"


class DeliveryOnlineStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class OrderStatus(str, enum.Enum):
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    PICKED_UP = "Picked Up"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CUSTOMER_NOT_AVAILABLE = "customer_not_available"
    CANCELLED = "cancelled"


class OrderPaymentMode(str, enum.Enum):
    UPI = "upi"
    ONLINE = "online"
    CASH = "cash"
    CREDIT = "credit"
    PRE_PAID = "pre-paid"
    CASH_ONLINE = "cash-online"


class OrderPaymentStatus(str, enum.Enum):
    PAID = "paid"
    PENDING = "pending"


class OrderUrgency(str, enum.Enum):
    NORMAL = "Normal"
    URGENT = "Urgent"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"


class InvoiceDocumentType(str, enum.Enum):
    INVOICE = "INVOICE"
    BILL = "BILL"


class InvoiceStatus(str, enum.Enum):
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    PAID = "PAID"
    FAILED = "FAILED"
    OVERDUE = "OVERDUE"
    VOID = "VOID"

