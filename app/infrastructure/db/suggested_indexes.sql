-- Suggested indexes for large-scale list/report queries (review against EXPLAIN
-- on production workloads before applying). Adjust table/column names to match your schema.

-- Example patterns (PostgreSQL):

-- CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_subscription_invoice_shop_status_created
--   ON subscription_invoices (shop_id, status, created_at DESC)
--   WHERE document_type = 'invoice';

-- CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_subscription_invoice_billing_period
--   ON subscription_invoices (billing_period_start, document_type);

-- CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_shop_owners_supermarket_active
--   ON shop_owners (is_supermarket, is_deleted, created_at DESC);

-- Foreign keys (orders.shop_id, orders.delivery_partner_id) often benefit from
-- indexes matching filter columns — see ix_orders_* in models/order.py.
