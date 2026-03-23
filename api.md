# Yadro Superadmin — API & Module Reference

This document lists all HTTP routes exposed by the superadmin backend, including the portal and monitor app. Routes are registered in `src/routers/index.js`.

**Last updated:** March 2026

---

## Route registration overview

| Base path | Router | Purpose |
|-----------|--------|---------|
| `/` | `rootRouter` | Root / landing |
| `/monitorapp` | `monitorappRouter` | Monitor app |
| `/auth` | `authRouter` | Superadmin authentication |
| `/portal` | `portalRouter` | Portal (shop owners) |
| `/dashboard` | `dashboardRouter` | Main dashboard |
| `/api/search` | `searchRouter` | Global search |
| `/api/report` | `reportRouter` | Report generation |
| `/delivery-partners` | `deliveryPartnerRouter` | Delivery partners |
| `/supermarkets/add` | `supermarketAddRouter` | Add supermarket flow (portal users allowed) |
| `/supermarkets` | `supermarketRouter` | Supermarkets |
| `/analytics` | `analyticsRouter` | Analytics |
| `/daily-activity` | `dailyActivityRouter` | Daily activity |
| `/api/v1/admin/invoices` | `invoiceRouter` | Invoices (superadmin + portal) |

---

## Authentication

| Auth type | Middleware | Used for |
|-----------|------------|----------|
| Superadmin session | `isAuthenticated` | Dashboard, supermarkets, analytics, delivery partners, etc. |
| Portal JWT | `isPortalAuthenticated` | Portal routes |
| Superadmin or portal | `isAuthenticatedOrPortal` | Invoice API |
| Admin API key | `validateAdminApiKey` | Cache rebuild / stats |
| Metrics API key | `validateMetricsApiKey` | Socket stats |
| Monitor app | `isMonitorAuthenticated` | Monitor app |

Portal users are typically restricted to `/portal/*`, `/supermarkets/add/*`, and `/api/v1/admin/invoices*` (see app middleware for exact rules).

---

## 1. Root (`/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root handler (redirect / render) |

**Router:** `src/routers/root.route.js`

---

## 2. Auth — Superadmin (`/auth`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/login` | Login page |
| GET | `/auth/logout` | Logout |
| POST | `/auth/logout` | Logout |
| POST | `/auth/send-otp` | Send OTP |
| POST | `/auth/verify-otp` | Verify OTP |

**Router:** `src/routers/auth.route.js`

---

## 3. Portal (`/portal`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/portal/login` | Portal login page |
| POST | `/portal/send-otp` | Send portal OTP |
| POST | `/portal/verify-otp` | Verify portal OTP |
| GET | `/portal/logout` | Portal logout |
| POST | `/portal/logout` | Portal logout |
| GET | `/portal/` | Redirect to `/portal/invoices` |

### Portal — invoices

| Method | Path | Description |
|--------|------|-------------|
| GET | `/portal/api/invoices` | List invoices |
| GET | `/portal/api/invoices/:id/download` | Download invoice |
| GET | `/portal/invoices` | Invoices page (UI) |

### Portal — shops

| Method | Path | Description |
|--------|------|-------------|
| GET | `/portal/shops` | Portal shops |

### Portal — daily activity

| Method | Path | Description |
|--------|------|-------------|
| GET | `/portal/daily-activity` | Daily activity page |
| GET | `/portal/daily-activity/api/data` | Daily activity data |
| GET | `/portal/daily-activity/api/export` | Daily activity CSV export |

### Portal — shop customers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/portal/shop-customers` | Shop customers page |
| GET | `/portal/shop-customers/api/shops` | Shops for customers |
| GET | `/portal/shop-customers/api/data` | Customer details |
| GET | `/portal/shop-customers/api/export/excel` | Excel export |
| GET | `/portal/shop-customers/api/export/pdf` | PDF export |
| GET | `/portal/shop-customers/api/segments` | Customer segments |
| GET | `/portal/shop-customers/api/export/segments/excel` | Segments Excel export |
| GET | `/portal/shop-customers/api/export/segments/pdf` | Segments PDF export |
| GET | `/portal/shop-customers/api/behaviour` | Behaviour data |
| GET | `/portal/shop-customers/api/behaviour/export/excel` | Behaviour Excel export |

**Router:** `src/routers/portal.route.js`

---

## 4. Dashboard (`/dashboard`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/` | Dashboard page |
| GET | `/dashboard/system-monitoring` | System monitoring |
| GET | `/dashboard/inventory-management` | Inventory management |
| GET | `/dashboard/invoices` | Invoices page |
| GET | `/dashboard/data` | Dashboard data |

### Dashboard — shop customers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/shop-customers` | Shop customers page |
| GET | `/dashboard/shop-customers/api/shops` | Shops |
| GET | `/dashboard/shop-customers/api/data` | Customer details |
| GET | `/dashboard/shop-customers/api/export/excel` | Excel export |
| GET | `/dashboard/shop-customers/api/export/pdf` | PDF export |
| GET | `/dashboard/shop-customers/api/segments` | Segments |
| GET | `/dashboard/shop-customers/api/export/segments/excel` | Segments Excel export |
| GET | `/dashboard/shop-customers/api/export/segments/pdf` | Segments PDF export |
| GET | `/dashboard/shop-customers/api/behaviour` | Behaviour data |
| GET | `/dashboard/shop-customers/api/behaviour/export/excel` | Behaviour Excel export |

### Dashboard — orders & entities

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/api/orders` | Filtered orders |
| GET | `/dashboard/api/shops` | All shops |
| GET | `/dashboard/api/orders/export/excel` | Orders Excel export |
| GET | `/dashboard/api/orders/export/pdf` | Orders PDF export |
| GET | `/dashboard/api/shop-owners` | Shop owners |
| GET | `/dashboard/api/delivery-partners` | Delivery partners |
| GET | `/dashboard/api/recent-activities` | Recent activities |

### Dashboard — payment & maintenance

| Method | Path | Description |
|--------|------|-------------|
| POST | `/dashboard/api/shop-owners/update-payment-status` | Update payment status |
| POST | `/dashboard/update-payment-status` | Form-based payment status update |
| POST | `/dashboard/api/superadmin/trigger-maintenance` | Trigger maintenance |
| GET | `/dashboard/api/superadmin/maintenance-cooldown` | Maintenance cooldown |

### Dashboard — admin / metrics (API key)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/dashboard/api/cache/rebuild` | Rebuild cache |
| GET | `/dashboard/api/socket-stats` | Socket stats |
| GET | `/dashboard/api/metrics/sockets/detailed` | Detailed socket metrics |
| GET | `/dashboard/api/cache/stats` | Cache stats |

**Router:** `src/routers/dashboard.route.js`

---

## 5. Search API (`/api/search`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search/` | Global search (`searchAll`) |

**Router:** `src/routers/search.route.js`

---

## 6. Report API (`/api/report`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/report/` | Generate report |

**Router:** `src/routers/report.route.js`

---

## 7. Delivery partners (`/delivery-partners`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/delivery-partners/` | List delivery partners |
| GET | `/delivery-partners/shop/:shop_id` | Shop delivery partners |
| GET | `/delivery-partners/details/:id` | Partner details |
| POST | `/delivery-partners/block/:id` | Block partner |
| POST | `/delivery-partners/update/:id` | Update partner |
| POST | `/delivery-partners/delete/:id` | Delete partner |
| POST | `/delivery-partners/restore/:id` | Restore partner |

**Router:** `src/routers/deliveryPartner.route.js`

---

## 8. Supermarkets — add flow (`/supermarkets/add`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/supermarkets/add/` | Redirect to step 1 |
| GET | `/supermarkets/add/step1` | Step 1 form |
| POST | `/supermarkets/add/step1` | Submit step 1 |
| GET | `/supermarkets/add/step2` | Step 2 form |
| POST | `/supermarkets/add/step2` | Submit step 2 |
| GET | `/supermarkets/add/step3` | Step 3 form (photo) |
| POST | `/supermarkets/add/step3` | Submit step 3 |
| GET | `/supermarkets/add/step4` | Step 4 form |
| POST | `/supermarkets/add/step4` | Submit step 4 |
| GET | `/supermarkets/add/summary` | Summary |
| POST | `/supermarkets/add/summary` | Submit summary |
| POST | `/supermarkets/add/block/:id` | Block supermarket |
| POST | `/supermarkets/add/unblock/:id` | Unblock supermarket |

**Router:** `src/routers/supermarketAdd.route.js`

---

## 9. Supermarkets (`/supermarkets`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/supermarkets/` | List supermarkets |
| GET | `/supermarkets/details/:shop_id` | Supermarket details |
| GET | `/supermarkets/details/:shop_id/pdf` | Supermarket PDF |
| GET | `/supermarkets/edit/:id` | Edit form |
| POST | `/supermarkets/edit/:id` | Handle edit (photo upload) |
| GET | `/supermarkets/orders/:shop_id` | Supermarket orders |
| GET | `/supermarkets/report` | Report download |
| GET | `/supermarkets/deleted` | Deleted supermarkets |
| GET | `/supermarkets/debug/test` | Debug test |
| GET | `/supermarkets/debug/db` | Debug DB |
| POST | `/supermarkets/delete/:id` | Soft delete |
| POST | `/supermarkets/restore/:id` | Restore |
| GET | `/supermarkets/api/check-shop-id` | Check shop ID |
| GET | `/supermarkets/api/check-user-id` | Check user ID |
| GET | `/supermarkets/api/v1/admin/supermarkets/:shop_id/order-statistics` | Order statistics |
| POST | `/supermarkets/api/subscription/:shop_id` | Create subscription |
| PATCH | `/supermarkets/api/subscription/:shop_id/amount` | Update subscription amount |

**Router:** `src/routers/supermarket.route.js`

---

## 10. Analytics (`/analytics`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/` | Analytics page |
| GET | `/analytics/supermarket` | Supermarket analytics |
| GET | `/analytics/market-study` | Market study analytics |
| POST | `/analytics/filter/update` | Update filter |
| GET | `/analytics/cache/get` | Get cache |
| POST | `/analytics/cache/set` | Set cache |
| GET | `/analytics/ratelimit/info` | Rate limit info |
| POST | `/analytics/ratelimit/increment` | Increment rate limit |
| POST | `/analytics/chart/download` | Download chart PDF |

**Router:** `src/routers/analytics.route.js`

---

## 11. Daily activity (`/daily-activity`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/daily-activity/` | Daily activity page |
| GET | `/daily-activity/api/data` | Daily activity data |
| GET | `/daily-activity/api/export` | CSV export |

**Router:** `src/routers/dailyActivity.route.js`

---

## 12. Invoice API (`/api/v1/admin/invoices`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/invoices/` | List invoices |
| GET | `/api/v1/admin/invoices/shops-with-subscriptions` | Shops with subscriptions |
| GET | `/api/v1/admin/invoices/monthly-summary` | Monthly summary |
| GET | `/api/v1/admin/invoices/:id` | Invoice details |
| GET | `/api/v1/admin/invoices/:id/download` | Download invoice |
| GET | `/api/v1/admin/invoices/:id/notes` | Invoice notes |
| POST | `/api/v1/admin/invoices/create-manual` | Create manual invoice |
| POST | `/api/v1/admin/invoices/create-manual-bill` | Create manual bill |
| POST | `/api/v1/admin/invoices/create-fully-manual` | Create fully manual invoice |
| POST | `/api/v1/admin/invoices/:id/notes` | Add note |
| PATCH | `/api/v1/admin/invoices/:id/status` | Update status |
| PATCH | `/api/v1/admin/invoices/:id` | Patch invoice |
| PUT | `/api/v1/admin/invoices/:id` | Update invoice |
| PATCH | `/api/v1/admin/invoices/:id/notes/delete` | Delete note |
| POST | `/api/v1/admin/invoices/:id/retry-bill` | Retry bill generation |
| POST | `/api/v1/admin/invoices/:id/issue` | Issue invoice |
| POST | `/api/v1/admin/invoices/:id/send-email` | Send invoice email |
| POST | `/api/v1/admin/invoices/:id/send-followup-email` | Send follow-up email |
| POST | `/api/v1/admin/invoices/generate-bills-for-paid` | Generate bills for paid |
| POST | `/api/v1/admin/invoices/generate-monthly` | Generate monthly invoices |
| POST | `/api/v1/admin/invoices/generate-monthly-for-month` | Generate for selected month |
| POST | `/api/v1/admin/invoices/run-status-automation` | Run status automation |
| POST | `/api/v1/admin/invoices/generate/:sub_id` | Generate for subscription |
| POST | `/api/v1/admin/invoices/create-dummy-data` | Create dummy data (disabled in production) |
| POST | `/api/v1/admin/invoices/sync-notes` | Sync notes |

**Router:** `src/routers/invoice.route.js`

> **Note:** Static routes (e.g. `shops-with-subscriptions`, `monthly-summary`) are defined before `/:id` routes in the router so they are matched correctly.

---

## 13. Monitor app (`/monitorapp`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/monitorapp/` | Root |
| GET | `/monitorapp/login` | Login page |
| POST | `/monitorapp/verify` | Verify password |
| GET | `/monitorapp/dashboard` | Dashboard |
| POST | `/monitorapp/verify-shop-password` | Verify shop password |
| POST | `/monitorapp/lock-shop-data` | Lock shop data |
| GET | `/monitorapp/download/shop-app` | Download shop app |
| GET | `/monitorapp/download/shop-app-x64` | Download shop app (x64) |
| GET | `/monitorapp/download/shop-app-x86` | Download shop app (x86) |
| GET | `/monitorapp/logout` | Logout |
| POST | `/monitorapp/logout` | Logout |

**Router:** `src/routers/monitorapp.route.js`

---

## Module → router file map

| Module | File |
|--------|------|
| Root | `src/routers/root.route.js` |
| Auth | `src/routers/auth.route.js` |
| Portal | `src/routers/portal.route.js` |
| Dashboard | `src/routers/dashboard.route.js` |
| Search | `src/routers/search.route.js` |
| Report | `src/routers/report.route.js` |
| Delivery partners | `src/routers/deliveryPartner.route.js` |
| Supermarkets | `src/routers/supermarket.route.js` |
| Supermarket add | `src/routers/supermarketAdd.route.js` |
| Analytics | `src/routers/analytics.route.js` |
| Daily activity | `src/routers/dailyActivity.route.js` |
| Invoices | `src/routers/invoice.route.js` |
| Monitor app | `src/routers/monitorapp.route.js` |

---

## Maintaining this document

When adding or changing routes, update the corresponding section and bump the “Last updated” date at the top. The source of truth is the `*.route.js` files under `src/routers/`.
