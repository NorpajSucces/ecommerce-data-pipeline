BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.monthly_order_summary AS
WITH order_item_totals AS (
    SELECT
        order_id,
        SUM(price) AS item_value
    FROM staging.order_items
    GROUP BY order_id
)
SELECT
    DATE_TRUNC('month', orders.order_purchase_timestamp)::DATE
        AS order_month,
    COUNT(*) AS order_count,
    SUM(order_item_totals.item_value) AS total_item_value
FROM staging.orders AS orders
INNER JOIN order_item_totals
    ON orders.order_id = order_item_totals.order_id
WHERE orders.order_status = 'delivered'
GROUP BY
    DATE_TRUNC('month', orders.order_purchase_timestamp)::DATE;

COMMIT;