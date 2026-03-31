## Sales → Shops reporting plan

### Goal
Build a **Sales → Shops** reporting module that shows:
- Shops created (signups) vs **actively using** ratio
- **Orders per day** and revenue per day
- “Which shops” insights: top active, newly created, and inactive/at-risk shops

### Definitions
- **Active shop**: shop has **≥ 1 DELIVERED order in last 30 days**
- **Time window UX**: **custom date range picker** with preset shortcuts

### What already exists (reuse first)
Backend endpoints already present:
- `backendIndianySuperadmin/app/api/v1/routers/sales_activity/routes.py`
  - `GET /api/v1/admin/sales-activity/overview?days=...` (signups + activation buckets)
  - `GET /api/v1/admin/sales-activity/monthly?months=...`
  - `GET /api/v1/admin/sales-activity/top-shops?limit=...`
- `backendIndianySuperadmin/app/api/v1/routers/daily_activity/routes.py`
  - `GET /api/v1/admin/daily-activity/trends?days=...` (orders + delivered revenue per day)
  - `GET /api/v1/admin/daily-activity/shops?...` (shop leaderboard for a single day)
- `backendIndianySuperadmin/app/api/v1/routers/analytics/routes.py`
  - `GET /analytics/reports/overview?days=...` (overall KPIs + `series` per day)
  - `GET /analytics/reports/shops?days=...&limit=...` (top shops)

Frontend page already present (can extend):
- `frontendSuperAdminIndia/frontendSuperadminIndia/src/pages/activity/SalesActivityPage.jsx`

### Gaps to fill (new data we need)
Your requested “**shops created vs actively using ratio**” is not exactly the same as the existing activation metric (time-to-first-order).
We will add a new backend endpoint that returns:
- Total shops created in the selected window
- Total shops active (≥1 **DELIVERED** order) in the last 30 days (or within window, depending on filter)
- Ratio + supporting lists

### New backend endpoint (admin)
Add: `GET /api/v1/admin/sales/shops/engagement`

- **Query**
  - `start` (ISO datetime)
  - `end` (ISO datetime)
  - `active_days` default 30
  - `limit` default 20 (for list sections)

- **Response**
  - `kpis`: `{ shops_created, shops_total, active_shops, active_ratio_pct, inactive_shops }`
  - `series_daily`: `[{date, orders, delivered_revenue, active_shops}]` for the selected window
  - `lists`
    - `top_shops_by_revenue` (limit)
    - `top_shops_by_orders` (limit)
    - `new_shops` (created in window)
    - `inactive_shops` (no delivered orders in last active_days)

Implementation approach:
- Reuse SQL patterns from:
  - `SalesActivityRepository.get_overview()` (shop created counting + cohort patterns)
  - `DailyActivityRepository.get_trends()` (daily orders + delivered revenue)

Files likely added/updated:
- Add `backendIndianySuperadmin/app/api/v1/routers/sales/shops_routes.py`
- Add `backendIndianySuperadmin/app/services/sales_shops_service.py`
- Add `backendIndianySuperadmin/app/repositories/sales_shops_repository.py`
- Register router in `backendIndianySuperadmin/app/api/v1/routers/protected.py`

### Frontend module design
Either extend `SalesActivityPage` or create a new `SalesShopsPage` with tabs:
- **Overview**: KPI cards + active ratio ring/pie + narrative (window summary)
- **Daily trend**: line chart for orders/day + delivered revenue/day
- **Shops**: table with filters + export CSV
  - Columns: shop name, user id, created_at, last_login_at (if available), delivered_orders_30d, delivered_revenue_30d, status
  - Sort: revenue desc, orders desc, newest, inactive

#### Custom date range picker
- Presets: Today, Last 7 days, Last 30 days, This month, Last month
- Uses `start/end` in URL query params so it’s shareable/bookmarkable

Frontend files likely:
- Add `frontendSuperAdminIndia/frontendSuperadminIndia/src/apis/salesShopsApi.js`
- Add `frontendSuperAdminIndia/frontendSuperadminIndia/src/pages/sales/SalesShopsPage.jsx` (or extend `SalesActivityPage.jsx`)
- Update sidebar nav to include a **Sales → Shops** entry (or reuse `activity.sales` route)

### Data flow
```mermaid
flowchart TD
SalesUI[SalesShopsPage] -->|GET engagement(start,end)| SalesEngagementApi
SalesEngagementApi --> BackendRouter[AdminSalesShopsRouter]
BackendRouter --> Repo[SalesShopsRepository]
Repo --> DB[(Postgres)]
SalesUI -->|GET daily-trends(days)| DailyActivityApi
SalesUI -->|GET reports/shops(days,limit)| AnalyticsReports
```

### Acceptance criteria
- Sales page shows:
  - Shops created in range
  - Active shops (delivered in last 30d) and ratio
  - Daily orders + delivered revenue chart for selected range
  - Tables for top/new/inactive shops with scroll + CSV export
- Empty-state handling (0 data) is clean and does not crash

### Test plan
- Hit new endpoint with a range that includes known delivered orders; confirm non-zero active ratio.
- Range with no delivered orders; confirm ratio is 0 and UI handles empty series.
- Confirm inactive list changes when delivered orders are added.

