# FastAPI Models Specification (for new project)

This document is a model-by-model guide to recreate the current backend data layer in a new **Python FastAPI** project.

It is based on existing Sequelize models and associations from:
- `src/models/*.js`
- `src/config/associations.js`

Use this as the source to implement:
1. SQLAlchemy ORM models
2. Pydantic schemas
3. Alembic migrations
4. Domain entities (if using clean architecture layers)

---

## 1) Model inventory (current system)

Core models:
1. `ShopOwner` (`shop_owners`)
2. `Address` (`addresses`)
3. `DeliveryPartner` (`delivery_partners`)
4. `Order` (`orders`)
5. `Subscription` (`subscriptions`)
6. `SubscriptionInvoice` (`subscription_invoices`)
7. `CustomerOrderAddress` (`customer_order_addresses`)
8. `ShopOwnerPromotion` (`shopowner_promotions`)

---

## 2) Relationships (must preserve)

From current associations:

1. `ShopOwner` -> `Address`
- many-to-one by `shop_owners.address_id -> addresses.id`

2. `ShopOwner` -> `DeliveryPartner`
- one-to-many by `shop_owners.shop_id -> delivery_partners.shop_id`

3. `ShopOwner` -> `Order`
- one-to-many by `shop_owners.shop_id -> orders.shop_id`

4. `Order` -> `DeliveryPartner`
- many-to-one by `orders.delivery_partner_id -> delivery_partners.delivery_partner_id`

5. `ShopOwner` -> `Subscription`
- one-to-one by `shop_owners.shop_id -> subscriptions.shop_id`

6. `Subscription` -> `SubscriptionInvoice`
- one-to-many by `subscriptions.subscription_id -> subscription_invoices.subscription_id`

7. `ShopOwner` -> `SubscriptionInvoice`
- one-to-many by `shop_owners.shop_id -> subscription_invoices.shop_id`

8. `ShopOwnerPromotion` -> `ShopOwner`
- one-to-one by `shopowner_promotions.shop_id -> shop_owners.shop_id`

---

## 3) SQLAlchemy model files (recommended)

Create these files in your FastAPI project:

```
app/infrastructure/db/models/
  base.py
  address.py
  shop_owner.py
  delivery_partner.py
  order.py
  subscription.py
  subscription_invoice.py
  customer_order_address.py
  shop_owner_promotion.py
  enums.py
```

Optional shared mixins:

```
app/infrastructure/db/models/mixins.py
  TimestampMixin
  SoftDeleteMixin
```

---

## 4) Detailed model specifications

> Notes:
> - Keep snake_case column names to stay migration-compatible.
> - Use `Numeric(10,2)`/`Numeric(15,2)` for money fields.
> - Use `DateTime(timezone=True)` for timestamp fields.
> - For PostgreSQL JSON fields, use `JSONB`.

### 4.1 `Address` (`addresses`)

Primary key:
- `id` (int, auto-increment)

Columns:
- `street_address` (varchar(250), required)
- `city` (varchar(100), required)
- `state` (varchar(100), required)
- `pincode` (varchar(20), required, usually 6-digit)
- `latitude` (numeric(10,6), nullable)
- `longitude` (numeric(10,6), nullable)
- `created_at`, `updated_at` (datetime)

Indexes:
- `pincode`
- `(city, state)`
- `(latitude, longitude)`

Validation rules:
- city/state alpha + spaces
- pincode numeric and expected length
- lat/lng valid ranges

---

### 4.2 `ShopOwner` (`shop_owners`)

Primary key:
- `id` (int, auto-increment)

Business identity:
- `shop_id` (varchar(50), unique, required)
- `user_id` (int, unique, required)

Columns (important):
- `shop_name` (varchar(200), required)
- `password` (varchar(255), required)
- `phone` (varchar(20), nullable)
- `email` (varchar(100), nullable; unique where not null)
- `shop_license_no` (varchar(100), nullable; unique)
- `photo` (varchar(255), nullable)
- `device_token` (varchar(512), nullable)
- `address_id` (int, FK to `addresses.id`, required)
- `subscription_id` (int, unique, nullable)
- `status` (enum: `active|inactive|suspended|blocked`, default `active`)
- `is_blocked` (bool, default false)
- `is_deleted` (bool, default false)
- `payment_status` (enum: `pending|paid|failed`, default `pending`)
- `contact_person_number` (varchar(20), nullable)
- `contact_person_email` (varchar(100), nullable)
- `is_sms_activated` (bool, default false)
- `single_sms` (bool, default false)
- `is_automated` (bool, default false)
- `whatsapp` (bool, default false)
- `block_reason` (text, nullable)
- `task_id` (varchar, nullable)
- `is_web_app` (bool, default true)
- `rating` (numeric(3,2), nullable, 0..5)
- `geo_coordinates` (json/jsonb, nullable)
- `auto_assigned` (bool, default false)
- `self_assigned` (bool, default false)
- `is_supermarket` (bool, default true)
- `last_login_at` (datetime, nullable)
- `hmac_secret` (varchar(128), unique nullable)
- `upi_id` (varchar(100), nullable)
- `delivery_time` (int, nullable, default 30)
- `created_at`, `updated_at`

Indexes:
- unique `shop_id`
- unique `user_id`
- unique partial `email` where not null
- `phone`
- `(status, is_deleted)`
- `address_id`
- unique partial `hmac_secret` where not null

---

### 4.3 `DeliveryPartner` (`delivery_partners`)

Primary key:
- `delivery_partner_id` (varchar(20))

Columns:
- `shop_id` (varchar(50), required; FK-like link to `shop_owners.shop_id`)
- `first_name` (varchar(100), required)
- `last_name` (varchar(100), nullable)
- `password` (varchar(255), required)
- `license_no` (varchar(100), unique, required)
- `license_image` (text/varchar(1000), required; JSON array string in old system)
- `govt_id_image` (text/varchar(1000), nullable; JSON array string in old system)
- `join_date` (datetime, default now)
- `is_blocked` (bool, default false)
- `current_status` (enum: `idle|order_assigned|ongoing`, default `idle`)
- `is_deleted` (bool, default false)
- `order_count` (int, default 0)
- `age` (int, required, 18..70)
- `phone1` (bigint, unique, required)
- `phone2` (bigint, unique nullable)
- `email` (varchar(100), nullable)
- `online_status` (enum: `online|offline`, default `offline`)
- `rating` (numeric(3,2), nullable)
- `photo` (varchar(1000), required)
- `device_token` (varchar(512), nullable)
- `device_id` (varchar(255), nullable)
- `last_login` (datetime, nullable)
- `last_order` (datetime, nullable)
- `vehicle_detail` (varchar(200), nullable)
- `total_bonus` (int, default 0)
- `total_penalty` (int, default 0)
- `liquid_cash` (numeric(10,2), default 0)
- `hmac_secret` (varchar(128), unique nullable)
- `created_at`, `updated_at`

Indexes:
- unique `delivery_partner_id`
- `(shop_id, current_status)`
- unique `license_no`
- `phone1`
- `(online_status, current_status)`
- `(shop_id, is_deleted)`
- partial `rating` where not null
- unique partial `hmac_secret` where not null

Important business rule:
- If `online_status == offline`, `current_status` should not remain assigned/ongoing.

---

### 4.4 `Order` (`orders`)

Primary key:
- `order_id` (int, auto-increment)

Columns (major):
- `shop_id` (varchar(50), required)
- `delivery_partner_id` (varchar(20), nullable)
- `address` (varchar(500), required)
- `bill_no` (varchar(100), nullable)
- `order_at` (datetime)
- `customer_name` (varchar(100), required)
- `customer_phone_number` (bigint, required)
- `total_amount` (numeric(10,2), required)
- `order_status` (enum: `Pending|Assigned|Picked Up|Out for Delivery|Delivered|customer_not_available|cancelled`)
- `payment_mode` (enum: `upi|online|cash|credit|pre-paid|cash-online`)
- `payment_status` (enum: `paid|pending`, default `pending`)
- `special_instructions` (text, nullable)
- `cancellation_reason` (text, nullable)
- `assigned_at`, `picked_up_at`, `delivered_at`, `cancelled_at` (datetime, nullable)
- `estimated_time_arrival` (datetime, nullable)
- `time_period` (varchar(50), nullable)
- `feedback` (text, nullable)
- `payment_proof` (varchar(1000), nullable)
- `bill_image` (varchar(1000), nullable)
- `payment_verification` (bool, default false)
- `upi_amount`, `online_amount`, `cash_amount`, `credit_amount`, `prepaid_amount` (numeric(10,2))
- `advanced_payment` (numeric(10,2), nullable)
- `utr` (varchar(100), nullable)
- `water` (bool, default false)
- `water_count` (int, default 0)
- `counter` (varchar(50), nullable)
- `urgency` (enum: `Normal|Urgent`, default `Normal`)
- `is_address_updated` (bool, default false)
- `tracking_token` (varchar(64), nullable)
- `tracking_token_expires_at` (datetime, nullable)
- `tracking_active` (bool, default false)
- `delivery_charge` (numeric(10,2), default 0)
- `is_deleted` (bool, default false)
- `order_rating` (int, nullable, 0..5)
- `order_feedback` (text, nullable, max 500)
- `feedback_token` (varchar(255), unique nullable)
- `pay_later` (bool, default false)
- `edited` (bool, default false)
- `is_blank_order` (bool, default false)
- `blank_order_at` (datetime, nullable)
- `notes` (jsonb, nullable)
- `created_at`, `updated_at`

Critical unique/constraints:
- unique partial on `(shop_id, bill_no)` where `is_deleted = false`

Critical indexes:
- `is_deleted`
- `(shop_id, is_deleted)`
- `(order_status, is_deleted)`
- `(delivery_partner_id, is_deleted)`
- `created_at`
- `(bill_no, is_deleted)`
- `(tracking_token, is_deleted)`
- `feedback_token`
- `(shop_id, order_status, is_deleted)`
- `(delivery_partner_id, order_status, is_deleted)`
- `(shop_id, created_at, is_deleted)`
- `(shop_id, delivered_at, is_deleted)`
- pay-later job/query composite indexes

---

### 4.5 `Subscription` (`subscriptions`)

Primary key:
- `subscription_id` (int, auto-increment)

Columns:
- `shop_id` (varchar(50), required)
- `start_date` (datetime, required)
- `end_date` (datetime, required)
- `amount` (numeric(10,2), required)
- `status` (enum: `active|expired|cancelled|past_due`, default `active`)
- `last_payment_date` (datetime, nullable)
- `created_at`, `updated_at`

Indexes:
- `shop_id`
- `status`
- `end_date`

---

### 4.6 `SubscriptionInvoice` (`subscription_invoices`)

Primary key:
- `invoice_id` (int, auto-increment)

Foreign keys:
- `subscription_id` -> `subscriptions.subscription_id` (required)
- `shop_id` -> `shop_owners.shop_id` (logical FK used heavily for quick queries)

Columns:
- `invoice_number` (varchar(50), unique, required)
- `billing_period_start` (datetime, required)
- `billing_period_end` (datetime, required)
- `amount` (numeric(10,2), required)
- `discount` (numeric(10,2), default 0)
- `other_charges` (numeric(10,2), default 0)
- `cgst`, `igst`, `sgst` (numeric(10,2), default 0)
- `description` (text, nullable)
- `notes` (text, nullable)
- `document_type` (enum: `INVOICE|BILL`, default `INVOICE`)
- `status` (enum: `PENDING|ISSUED|PAID|FAILED|OVERDUE|VOID`, default `PENDING`)
- `pdf_url` (varchar(500), nullable)
- `transaction_reference` (varchar(100), nullable)
- `paid_at` (datetime, nullable)
- `bank_details` (jsonb, nullable)
- `created_at`, `updated_at`

Critical unique constraint:
- `(shop_id, billing_period_start, document_type)` unique
  (prevents duplicate invoice/bill per shop+period+doc type)

Indexes:
- `shop_id`
- `subscription_id`
- `status`
- unique `invoice_number`

---

### 4.7 `CustomerOrderAddress` (`customer_order_addresses`)

Primary key:
- `id` (int, auto-increment)

Columns:
- `customer_name` (varchar(255), required)
- `customer_phone_number` (bigint, required)
- `address` (text, required)
- `latitude` (numeric(10,6), nullable)
- `longitude` (numeric(10,6), nullable)
- `shop_id` (varchar(50), required)
- `credit_balance` (numeric(15,2), default 0)
- `debit_balance` (numeric(15,2), default 0)
- `current_month_order_count` (int, default 0)
- `previous_month_order_count` (int, default 0)
- `current_month_total_amount` (numeric(15,2), default 0)
- `previous_month_total_amount` (numeric(15,2), default 0)
- `current_month_tracked` (varchar(7), nullable, `YYYY-MM`)
- `previous_month_tracked` (varchar(7), nullable, `YYYY-MM`)
- `pay_later` (bool, default false)
- `is_deleted` (bool, default false)
- `created_at`, `updated_at`

Critical unique:
- `(customer_phone_number, shop_id)` unique

Important rule:
- latitude and longitude should be both present or both null.

Indexes:
- phone, name, coordinates, is_deleted, created_at, shop_id
- credit/debit balance indexes
- pay_later index
- customer stats composite indexes

---

### 4.8 `ShopOwnerPromotion` (`shopowner_promotions`)

Primary key:
- `id` (int, auto-increment)

Columns:
- `shop_id` (varchar(50), unique, required, references `shop_owners.shop_id`)
- `promotion_link` (varchar(512), nullable)
- `promotion_header` (varchar(255), nullable)
- `promotion_content` (text, nullable)
- `promotion_image_s3_key` (varchar(512), nullable)
- `is_marketing_enabled` (bool, default false)
- `created_at`, `updated_at`

Indexes:
- unique `shop_id`

---

## 5) Enum definitions (recommended central file)

Create in `app/infrastructure/db/models/enums.py`:
- `ShopStatus`: active/inactive/suspended/blocked
- `ShopPaymentStatus`: pending/paid/failed
- `DeliveryPartnerStatus`: idle/order_assigned/ongoing
- `DeliveryOnlineStatus`: online/offline
- `OrderStatus`: Pending/Assigned/Picked Up/Out for Delivery/Delivered/customer_not_available/cancelled
- `OrderPaymentMode`: upi/online/cash/credit/pre-paid/cash-online
- `OrderPaymentStatus`: paid/pending
- `OrderUrgency`: Normal/Urgent
- `SubscriptionStatus`: active/expired/cancelled/past_due
- `InvoiceDocumentType`: INVOICE/BILL
- `InvoiceStatus`: PENDING/ISSUED/PAID/FAILED/OVERDUE/VOID

---

## 6) Pydantic schema files (recommended)

Create per model:

```
app/api/v1/schemas/
  address.py
  shop_owner.py
  delivery_partner.py
  order.py
  subscription.py
  invoice.py
  customer_order_address.py
  shop_owner_promotion.py
```

For each model define:
1. `Create` schema (required create fields)
2. `Update` schema (all optional)
3. `Read` schema (response model with id/timestamps)
4. `ListItem` schema (smaller payload for list endpoints)

---

## 7) Migration order (Alembic)

Use this order to avoid FK issues:
1. `addresses`
2. `shop_owners`
3. `delivery_partners`
4. `orders`
5. `subscriptions`
6. `subscription_invoices`
7. `customer_order_addresses`
8. `shopowner_promotions`

Then add indexes/unique constraints (especially heavy `orders` indexes) in the same or follow-up migration.

---

## 8) Minimal “must-have first” model set

If you want to start quickly and expand:
Phase 1:
- `ShopOwner`
- `DeliveryPartner`
- `Order`
- `Subscription`
- `SubscriptionInvoice`

Phase 2:
- `Address`
- `CustomerOrderAddress`
- `ShopOwnerPromotion`

---

## 9) Compatibility notes for new project

1. Old project stores some JSON arrays in string fields (`license_image`, `govt_id_image`).
   - Prefer JSONB in new schema (or preserve string for zero-risk migration).
2. Keep soft delete behavior (`is_deleted`) because many queries depend on it.
3. Preserve key composite indexes in `orders` for dashboard/report performance.
4. Keep invoice idempotency unique constraint (`shop_id + billing_period_start + document_type`).
5. Preserve unique business IDs (`shop_id`, `delivery_partner_id`, `invoice_number`).

---

## 10) Source-of-truth files used

- `src/models/Address.js`
- `src/models/ShopOwner.js`
- `src/models/DeliveryPartner.js`
- `src/models/order.model.js`
- `src/models/Subscription.js`
- `src/models/SubscriptionInvoice.js`
- `src/models/customerorderAddress.js`
- `src/models/shopownerPromotion.model.js`
- `src/config/associations.js`

