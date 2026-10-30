BEGIN;

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE IF NOT EXISTS staging.orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL
        REFERENCES staging.customers (customer_id),
    order_status TEXT NOT NULL,
    order_purchase_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    order_approved_at TIMESTAMP WITHOUT TIME ZONE,
    order_delivered_carrier_date TIMESTAMP WITHOUT TIME ZONE,
    order_delivered_customer_date TIMESTAMP WITHOUT TIME ZONE,
    order_estimated_delivery_date TIMESTAMP WITHOUT TIME ZONE
);

CREATE TABLE IF NOT EXISTS staging.order_items (
    order_id TEXT NOT NULL
        REFERENCES staging.orders (order_id),
    order_item_id INTEGER NOT NULL,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TIMESTAMP WITHOUT TIME ZONE,
    price NUMERIC NOT NULL,
    freight_value NUMERIC,
    PRIMARY KEY (order_id, order_item_id)
);

COMMIT;