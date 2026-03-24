# Dashboard APIs - Detailed Specification (Backend Team Handoff)

This document contains **only dashboard module APIs** and explains:
1. endpoint contract (method/path/auth/query/body)
2. expected behavior
3. models/tables required per endpoint
4. implementation notes for new FastAPI backend

Base route: `/dashboard`

Source mapped from:
- `src/routers/dashboard.route.js`
- `src/controllers/dashboard.controller.js`
- `src/controllers/shopCustomers.controller.js`
- `src/controllers/ordersExport.controller.js`
- `src/controllers/superadmin.controller.js`

---

## 1) Auth and security rules

Dashboard endpoints use three auth modes:

1. **Superadmin session auth**
- Legacy middleware: `isAuthenticated`
- Use for most `/dashboard/*` and `/dashboard/api/*`

2. **Admin API key auth**
- Legacy middleware: `validateAdminApiKey`
- Header: `x-api-key`
- Used for cache ops endpoints

3. **Metrics API key auth**
- Legacy middleware: `validateMetricsApiKey`
- Header: `x-api-key`
- Used for socket metrics endpoints

### FastAPI recommendation
- Keep separate dependencies:
  - `Depends(require_superadmin())`
  - `Depends(require_admin_api_key())`
  - `Depends(require_metrics_api_key())`

---

## 2) Models used in dashboard module

Primary data models/tables:

1. `ShopOwner` -> `shop_owners`
2. `Address` -> `addresses`
3. `DeliveryPartner` -> `delivery_partners`
4. `Order` -> `orders`
5. `CustomerOrderAddress` -> `customer_order_addresses` (via customer services)
6. `Subscription` -> `subscriptions` (indirectly for invoice/inventory data in dashboard views)
7. `SubscriptionInvoice` -> `subscription_invoices` (indirectly for invoices page data)

Related services/integrations used by dashboard endpoints:
- chart rendering services (PDF/analytics exports)
- browser pool (PDF generation)
- cache service (for cache endpoints; placeholder in current code)
- socket server runtime metrics (`global.io` in Node)
- maintenance notification workflow (email + cooldown state)

---

## 3) Endpoint-by-endpoint API details

## A) Dashboard base and pages

### 3.1 GET `/dashboard/`
- **Auth:** Superadmin
- **Purpose:** Returns dashboard page data (legacy rendered page) including KPI widgets, recent orders, recent activities, and shop warning/exceeded thresholds.
- **Query params:** none (legacy)
- **Response (target in new backend):**
  - `stats`
  - `recentOrders`
  - `ordersData` (7-day trend)
  - `shopOwners` (latest)
  - `warningShops`, `exceededShops`
  - `activities`

**Models used**
- Read `shop_owners` (counts + latest shops + status)
- Read `addresses` (shop city/address)
- Read `orders` (counts by status + recent + 7-day trend + monthly counts)
- Read `delivery_partners` (counts)

**DB operations**
- Aggregate counts on `orders` by status/date
- Join `orders` with `shop_owners` and `delivery_partners`
- Join `shop_owners` with `addresses`

---

### 3.2 GET `/dashboard/system-monitoring`
- **Auth:** Superadmin
- **Purpose:** System monitoring view data route.
- **Models used:** none mandatory (current handler is mostly render-level)
- **FastAPI note:** return health/monitoring metadata JSON if frontend is separate.

---

### 3.3 GET `/dashboard/inventory-management`
- **Auth:** Superadmin
- **Purpose:** Inventory management view data.
- **Models used:** mostly `shop_owners` (payment/status/inventory-oriented screen)

---

### 3.4 GET `/dashboard/invoices`
- **Auth:** Superadmin
- **Purpose:** Dashboard invoices page data entry.
- **Models used:** `subscription_invoices`, `subscriptions`, `shop_owners` (via invoice module)

---

## B) Core dashboard data APIs

### 3.5 GET `/dashboard/data`
- **Auth:** Superadmin
- **Purpose:** API for dashboard frontend caching and bulk dashboard data retrieval.
- **Timeout:** extended/long timeout in legacy code.
- **Typical response:** summary KPI + charts + activity snapshots.

**Models used**
- `orders` (main source of KPIs/charts)
- `shop_owners` (totals/active)
- `delivery_partners` (totals/active)
- optional `addresses` for shop metadata

---

### 3.6 GET `/dashboard/api/orders`
- **Auth:** Superadmin
- **Purpose:** Fetch filtered orders for dashboard table.
- **Query params (commonly expected):**
  - `shop_ids` (comma-separated shop ids)
  - `order_status`
  - `payment_status`
  - `dateFrom`
  - `dateTo`
  - pagination/sorting fields (implementation-defined)

**Models used**
- `orders` (primary)
- `shop_owners` (for names/details via join)
- `delivery_partners` (for assigned partner info, optional)

**Important filter behavior**
- Always enforce `is_deleted = false` where business requires active orders.
- End date should be inclusive (set to 23:59:59.999).

---

### 3.7 GET `/dashboard/api/shops`
- **Auth:** Superadmin
- **Purpose:** Return all shops for dropdown filters.
- **Models used:** `shop_owners` (+ `addresses` optional)
- **Response fields:** at least `shop_id`, `shop_name`

---

### 3.8 GET `/dashboard/api/shop-owners`
- **Auth:** Superadmin (should be protected in new backend)
- **Purpose:** Paginated shop owner list.
- **Query params:**
  - `page` (default 1)
  - `limit` (default 5)
- **Response:** `shopOwners`, `totalPages`, `currentPage`

**Models used**
- `shop_owners` (read)
- `addresses` (joined as `address`)

---

### 3.9 GET `/dashboard/api/delivery-partners`
- **Auth:** Superadmin (should be protected in new backend)
- **Purpose:** Paginated delivery partner list.
- **Query params:**
  - `page` (default 1)
  - `limit` (default 5)
- **Response:** list + pagination metadata

**Models used**
- `delivery_partners` (read)

**Additional logic**
- Photo URL post-processing (`processImageField` equivalent in new backend)

---

### 3.10 GET `/dashboard/api/recent-activities`
- **Auth:** Superadmin (should be protected in new backend)
- **Purpose:** Recent activity feed (supermarkets added + delivery partners joined).
- **Query params:**
  - `page` (default 1)
  - `limit` (default 5)
  - `viewAll` (`true|false`)
- **Response:** `total`, `page`, `limit`, `activities[]`

**Models used**
- `shop_owners` (read created records)
- `delivery_partners` (read created records)

**Implementation behavior**
- Query only recent window (legacy uses last 7 days)
- Union both sources, sort by created_at desc
- Build `targetUrl`:
  - supermarkets -> `/supermarkets/details/{shop_id}`
  - delivery partners -> `/delivery-partners/details/{delivery_partner_id}`

---

## C) Dashboard orders exports

### 3.11 GET `/dashboard/api/orders/export/excel`
- **Auth:** Superadmin
- **Purpose:** Download orders analytics report in Excel.
- **Query params:** same as `/dashboard/api/orders` filters.
- **Response:** binary `.xlsx`

**Models used**
- `orders` (aggregate + timeline + status/payment breakdown)
- `shop_owners` (shop names for top shops/selected shops)

---

### 3.12 GET `/dashboard/api/orders/export/pdf`
- **Auth:** Superadmin
- **Purpose:** Download orders analytics report in PDF (charts included).
- **Query params:** same as `/dashboard/api/orders` filters.
- **Response:** binary `.pdf`

**Models used**
- `orders`
- `shop_owners`

**Services/integrations**
- chart rendering
- headless browser/pdf renderer

---

## D) Dashboard shop-customers APIs

These are mounted under dashboard but powered by shop-customer services.

### 3.13 GET `/dashboard/shop-customers`
- **Auth:** Superadmin
- **Purpose:** UI route/data bootstrap for shop customers module.
- **Models used:** none directly in router; service-backed.

---

### 3.14 GET `/dashboard/shop-customers/api/shops`
- **Auth:** Superadmin
- **Purpose:** Fetch shops allowed for customer analytics.
- **Models used**
- `shop_owners`

---

### 3.15 GET `/dashboard/shop-customers/api/data`
- **Auth:** Superadmin
- **Purpose:** Customer details analytics by shop + date/month range.
- **Query params:**
  - required: `shop_id`
  - either:
    - `start_date`, `end_date`
    - OR `start_month`, `end_month`
- **Response:** `shopName`, `dateRange`, `monthLabels`, `customers`

**Models used**
- Primary: `orders`
- Aggregated customer source: `customer_order_addresses`
- Shop validation/access: `shop_owners`

---

### 3.16 GET `/dashboard/shop-customers/api/export/excel`
- **Auth:** Superadmin
- **Purpose:** Export customer details to Excel.
- **Query params:** `shop_id`, `start_date`, `end_date`
- **Response:** `.xlsx`

**Models used**
- `customer_order_addresses` / `orders` aggregated data
- `shop_owners`

---

### 3.17 GET `/dashboard/shop-customers/api/export/pdf`
- **Auth:** Superadmin
- **Purpose:** Export customer details report to PDF.
- **Query params:** `shop_id`, `start_date`, `end_date`
- **Response:** `.pdf`

**Models used**
- `customer_order_addresses` / `orders`
- `shop_owners`

---

### 3.18 GET `/dashboard/shop-customers/api/segments`
- **Auth:** Superadmin
- **Purpose:** Customer segmentation analytics.
- **Query params:** shop + month/date inputs (service validated)
- **Response:** segment groups and metrics

**Models used**
- `orders`
- `customer_order_addresses`
- `shop_owners`

---

### 3.19 GET `/dashboard/shop-customers/api/export/segments/excel`
- **Auth:** Superadmin
- **Purpose:** Export customer segments to Excel.
- **Models used:** same as segments endpoint.

---

### 3.20 GET `/dashboard/shop-customers/api/export/segments/pdf`
- **Auth:** Superadmin
- **Purpose:** Export customer segments to PDF.
- **Models used:** same as segments endpoint.

---

### 3.21 GET `/dashboard/shop-customers/api/behaviour`
- **Auth:** Superadmin
- **Purpose:** Customer behaviour analytics.
- **Models used**
- `orders`
- `customer_order_addresses`
- `shop_owners`

---

### 3.22 GET `/dashboard/shop-customers/api/behaviour/export/excel`
- **Auth:** Superadmin
- **Purpose:** Export customer behaviour report to Excel.
- **Models used:** same as behaviour endpoint.

---

## E) Dashboard operations / admin actions

### 3.23 POST `/dashboard/api/shop-owners/update-payment-status`
- **Auth:** Superadmin (must enforce in new backend)
- **Purpose:** Update a shop owner payment status.
- **Body (expected):**
```json
{
  "shop_id": "SHOP001",
  "payment_status": "pending|paid|failed"
}
```

**Models used**
- `shop_owners` (write `payment_status`)

**Validation**
- `shop_id` required, existing
- `payment_status` enum-validated

---

### 3.24 POST `/dashboard/update-payment-status`
- **Auth:** Superadmin
- **Purpose:** Form compatibility endpoint that internally calls payment status update.
- **Body:** same as above
- **FastAPI recommendation:** keep temporarily for compatibility; frontend should migrate to `/api/shop-owners/update-payment-status`.

**Models used**
- `shop_owners` (write)

---

### 3.25 POST `/dashboard/api/superadmin/trigger-maintenance`
- **Auth:** Superadmin
- **Purpose:** Trigger maintenance notification flow to shop owners.
- **Body fields:**
  - `date` (`YYYY-MM-DD`)
  - `startTime` (`HH:mm`)
  - `endTime` (`HH:mm`)
  - `subject`
  - `body`
- **Response:** success/failure + stats

**Models used**
- `shop_owners` (read active shops/emails)

**External dependencies**
- SMTP provider / email service
- maintenance cooldown state store (in-memory or Redis/DB)

---

### 3.26 GET `/dashboard/api/superadmin/maintenance-cooldown`
- **Auth:** Superadmin
- **Purpose:** Fetch cooldown state for maintenance trigger.
- **Models used:** none required (state store only)

---

## F) Dashboard cache/metrics technical endpoints

### 3.27 POST `/dashboard/api/cache/rebuild`
- **Auth:** Admin API key
- **Purpose:** Trigger cache rebuild job.
- **Models used:** none directly; indirect depending on cache warm strategy.

---

### 3.28 GET `/dashboard/api/cache/stats`
- **Auth:** Admin API key
- **Purpose:** Return cache usage/hit-rate stats.
- **Models used:** none directly.

---

### 3.29 GET `/dashboard/api/socket-stats`
- **Auth:** Metrics API key
- **Purpose:** Basic socket connection metrics.
- **Models used:** none (runtime metrics only).

---

### 3.30 GET `/dashboard/api/metrics/sockets/detailed`
- **Auth:** Metrics API key
- **Purpose:** Detailed socket runtime metrics (rooms, transport, ping config).
- **Models used:** none.

---

## 4) Model usage matrix (quick view)

| Endpoint group | ShopOwner | Address | DeliveryPartner | Order | CustomerOrderAddress | Subscription | SubscriptionInvoice |
|---|---:|---:|---:|---:|---:|---:|---:|
| `/dashboard/`, `/dashboard/data` | R | R | R | R |  |  |  |
| `/dashboard/api/orders*` | R |  | (R optional) | R |  |  |  |
| `/dashboard/api/shops` | R | (R optional) |  |  |  |  |  |
| `/dashboard/api/shop-owners` | R | R |  |  |  |  |  |
| `/dashboard/api/delivery-partners` |  |  | R |  |  |  |  |
| `/dashboard/api/recent-activities` | R |  | R |  |  |  |  |
| `/dashboard/shop-customers/api/*` | R |  |  | R | R |  |  |
| `/dashboard/api/shop-owners/update-payment-status` | W |  |  |  |  |  |  |
| `/dashboard/invoices` | R |  |  |  |  | R | R |
| maintenance trigger/cooldown | R |  |  |  |  |  |  |
| cache/socket metrics endpoints |  |  |  |  |  |  |  |

R = read, W = write

---

## 5) FastAPI implementation structure (dashboard module)

Recommended files:

```
app/api/v1/routers/dashboard.py
app/api/v1/schemas/dashboard.py
app/application/use_cases/dashboard/
  get_dashboard_data.py
  get_filtered_orders.py
  list_shop_owners.py
  list_delivery_partners.py
  list_recent_activities.py
  update_shop_payment_status.py
  trigger_maintenance.py
  get_maintenance_cooldown.py
app/application/use_cases/dashboard_shop_customers/
  get_customer_details.py
  get_customer_segments.py
  get_customer_behaviour.py
  export_customer_excel.py
  export_customer_pdf.py
  export_segment_excel.py
  export_segment_pdf.py
  export_behaviour_excel.py
app/application/use_cases/dashboard_exports/
  export_orders_excel.py
  export_orders_pdf.py
```

Repository interfaces needed:
- `ShopOwnerRepository`
- `AddressRepository`
- `DeliveryPartnerRepository`
- `OrderRepository`
- `CustomerAnalyticsRepository` (customer_order_addresses + order aggregations)
- `MaintenanceNotificationService`
- `CacheAdminService`
- `SocketMetricsService`

---

## 6) Validation and contract checklist (must enforce)

1. Pagination defaults for list endpoints (`page`, `limit`)
2. Date filters:
- parse safely
- inclusive `dateTo` end-of-day behavior
3. Enum validation:
- `order_status`, `payment_status`, shop payment status
4. Export endpoints:
- correct content type + filename
5. Access control:
- lock non-superadmin endpoints properly (some legacy handlers are open in route file; tighten in new backend)
6. Soft delete:
- apply `is_deleted = false` where required

---

## 7) Notes for migration from legacy render routes

Legacy routes like:
- `/dashboard/`
- `/dashboard/shop-customers`
- `/dashboard/inventory-management`
- `/dashboard/invoices`

currently return rendered pages. In the new backend/frontend split:
- convert these to JSON payload endpoints or deprecate them,
- move page rendering and composition to frontend app.

