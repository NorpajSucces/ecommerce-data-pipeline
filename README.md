# E-Commerce Data Pipeline

A local batch data pipeline that loads Olist e-commerce CSV files into
PostgreSQL and produces independently verified monthly transaction summaries.

## Problem

Order, customer, and item records are distributed across separate CSV files.
An analyst needs a consistent monthly summary with clearly defined metrics
and checks against the source data.

## Pipeline

CSV files → Python profiling → PostgreSQL staging tables
→ SQL monthly summary view → independent CSV reconciliation

## Stack

- Python 3.13.14 and uv
- Psycopg 3
- PostgreSQL 17
- Docker Compose
- SQL

## Dataset

Source: [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

Download and extract the dataset, then place these files in `data/raw/`:

- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`

Raw datasets are excluded from Git.

## Data Dictionary

This reference follows the table definitions in
[`sql/001_create_staging.sql`](sql/001_create_staging.sql) and the view in
[`sql/002_create_monthly_summary.sql`](sql/002_create_monthly_summary.sql).
`Nullable` describes whether the database column accepts SQL NULL; it does not
describe how many missing values were observed during profiling.
All `TIMESTAMP` columns below are `TIMESTAMP WITHOUT TIME ZONE`.

### staging.customers

- Source: `olist_customers_dataset.csv`.
- Grain: one source customer record per `customer_id`.
- Primary key: `customer_id`.

| Column | PostgreSQL type | Nullable | Description |
|---|---|---|---|
| `customer_id` | `TEXT` | No | Customer-record identifier used to join with `staging.orders.customer_id`. |
| `customer_unique_id` | `TEXT` | Yes | Identifier used to recognize the same customer across orders; not declared UNIQUE in this schema. |
| `customer_zip_code_prefix` | `TEXT` | Yes | Customer postal-code prefix, stored as text to preserve leading zeros. |
| `customer_city` | `TEXT` | Yes | Customer city. |
| `customer_state` | `TEXT` | Yes | Customer state abbreviation. |

Use `customer_id` for the order-to-customer JOIN. Use `customer_unique_id` when
studying repeat customers; counting customer records alone does not establish
the number of distinct people.

### staging.orders

- Source: `olist_orders_dataset.csv`.
- Grain: one row per order.
- Primary key: `order_id`.
- Foreign key: `customer_id` references `staging.customers.customer_id`.

| Column | PostgreSQL type | Nullable | Description |
|---|---|---|---|
| `order_id` | `TEXT` | No | Order identifier used to join with `staging.order_items.order_id`. |
| `customer_id` | `TEXT` | No | Reference to the customer record associated with the order. |
| `order_status` | `TEXT` | No | Order status in the historical dataset snapshot. |
| `order_purchase_timestamp` | `TIMESTAMP` | No | Purchase timestamp used to determine the month in the analytical summary. |
| `order_approved_at` | `TIMESTAMP` | Yes | Order approval timestamp. |
| `order_delivered_carrier_date` | `TIMESTAMP` | Yes | Timestamp when the order was handed to the carrier. |
| `order_delivered_customer_date` | `TIMESTAMP` | Yes | Actual delivery timestamp to the customer. |
| `order_estimated_delivery_date` | `TIMESTAMP` | Yes | Estimated customer delivery date. |

Observed source statuses: `delivered`, `shipped`, `canceled`, `unavailable`,
`invoiced`, `processing`, `created`, and `approved`.
The column is TEXT; the schema does not restrict it to this list.

### staging.order_items

- Source: `olist_order_items_dataset.csv`.
- Grain: one item row within an order; an order can contain multiple item rows.
- Composite primary key: (`order_id`, `order_item_id`).
- Foreign key: `order_id` references `staging.orders.order_id`.

| Column | PostgreSQL type | Nullable | Description |
|---|---|---|---|
| `order_id` | `TEXT` | No | Reference to the parent order; can repeat across different item rows. |
| `order_item_id` | `INTEGER` | No | Item identifier within an order; only unique together with `order_id`. |
| `product_id` | `TEXT` | Yes | Product identifier from the source dataset. |
| `seller_id` | `TEXT` | Yes | Seller identifier from the source dataset. |
| `shipping_limit_date` | `TIMESTAMP` | Yes | Seller shipping deadline. |
| `price` | `NUMERIC` | No | Item price included in the monthly `total_item_value` metric. |
| `freight_value` | `NUMERIC` | Yes | Freight amount associated with the item; excluded from `total_item_value`. |

V1 does not load the products or sellers tables, so `product_id` and `seller_id`
have no database foreign-key constraints here.
Item-row count and distinct-product count are different measures; the same
product can appear in multiple item rows.

### analytics.monthly_order_summary

- Object type: view.
- Grain: one row per purchase month represented by delivered orders.
- Source: `staging.orders` joined with item totals aggregated per order.
- Months without delivered orders are omitted.

| Column | PostgreSQL type | Description |
|---|---|---|
| `order_month` | `DATE` | First day of the purchase month, derived from `order_purchase_timestamp`. |
| `order_count` | `BIGINT` | Number of delivered orders purchased in the month, counting each order once. |
| `total_item_value` | `NUMERIC` | Sum of item prices for those orders, excluding freight. |

The view derives its rows from staging when queried; it is not a separate
physical copy of the summary data.

### Relationships and JOIN Keys

| Referencing column | Referenced column |
|---|---|
| `staging.orders.customer_id` | `staging.customers.customer_id` |
| `staging.order_items.order_id` | `staging.orders.order_id` |

Each order references one customer record, and each item references one order.
When orders are joined to items, order-level fields repeat for each item.
For order counts, use `COUNT(DISTINCT orders.order_id)` or aggregate items to one
row per order before counting, as the monthly summary does.

### Query Examples for pgAdmin

Preview delivered order items together with order and customer information.
The result has one row per item, not one row per order:

```sql
SELECT
    orders.order_id,
    orders.order_purchase_timestamp,
    customers.customer_city,
    customers.customer_state,
    items.order_item_id,
    items.product_id,
    items.price,
    items.freight_value
FROM staging.orders AS orders
INNER JOIN staging.customers AS customers
    ON orders.customer_id = customers.customer_id
INNER JOIN staging.order_items AS items
    ON orders.order_id = items.order_id
WHERE orders.order_status = 'delivered'
ORDER BY orders.order_id, items.order_item_id
LIMIT 20;
```

Read the monthly analytical output:

```sql
SELECT order_month, order_count, total_item_value
FROM analytics.monthly_order_summary
ORDER BY order_month;
```

## Analytical Rules

- Include orders with status `delivered` in the dataset snapshot.
- Group orders by purchase month using `order_purchase_timestamp`.
- Sum item prices, excluding freight.
- Aggregate items per order before counting orders.
- Omit months without delivered orders.
- Preserve all source order statuses in staging.

Output: `analytics.monthly_order_summary`.

## Verified Results

| Check | Result |
|---|---:|
| Customers loaded | 99,441 |
| Orders loaded | 99,441 |
| Order items loaded | 112,650 |
| Months reconciled | 23 |
| Delivered orders | 96,478 |
| Total item value | 13221498.11 |

Each month's order count and item value matched an independent calculation
from the source CSV files using Python and Decimal.

## Fresh Setup — PowerShell

Prerequisites: Git, uv, and Docker Desktop with the Engine running.

### 1. Clone and install dependencies

```powershell
git clone https://github.com/NorpajSucces/ecommerce-data-pipeline.git
Set-Location ecommerce-data-pipeline
uv sync --locked
```

### 2. Configure the local environment

For a new clone:

```powershell
Copy-Item .env.example .env
```

Set a unique `POSTGRES_PASSWORD` in `.env`.
Keep the example database/user `ecommerce` for the commands below.

The default connection from Python is `127.0.0.1:5433`.
The `.env` file is excluded from Git.

Create `data/raw/` and add the three CSV files listed above.

### 3. Profile the source data

```powershell
uv run python scripts/inspect_orders.py
uv run python scripts/inspect_customers.py
uv run python scripts/inspect_order_items.py
```

### 4. Start PostgreSQL and create staging tables

```powershell
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d --wait
```

```powershell
Get-Content -Raw .\sql\001_create_staging.sql | docker compose --env-file .env exec -T postgres psql -U ecommerce -d ecommerce -v ON_ERROR_STOP=1
```

Check the Python connection:

```powershell
uv run --env-file .env python scripts/check_database_connection.py
```

### 5. Perform the initial load

Load in foreign-key dependency order:

```powershell
uv run --env-file .env python scripts/load_customers.py
uv run --env-file .env python scripts/load_orders.py
uv run --env-file .env python scripts/load_order_items.py
```

Loaders require empty target tables. Each load runs in a transaction and
checks the source and database row counts before committing.

Empty CSV fields become SQL NULL. Malformed records and database constraint
violations stop the transaction.

### 6. Create the monthly summary

```powershell
Get-Content -Raw .\sql\002_create_monthly_summary.sql | docker compose --env-file .env exec -T postgres psql -U ecommerce -d ecommerce -v ON_ERROR_STOP=1
```

### 7. Reconcile against the source CSV files

```powershell
uv run --env-file .env python scripts/verify_monthly_summary.py
```

Expected result: reconciliation passes for 23 months, 96,478 delivered orders,
and total item value of 13221498.11.

Inspect the output:

```powershell
docker compose --env-file .env exec postgres psql -U ecommerce -d ecommerce -c "SELECT * FROM analytics.monthly_order_summary ORDER BY order_month;"
```

## Resuming an Existing Setup

Start PostgreSQL and rerun verification:

```powershell
docker compose --env-file .env up -d --wait
uv run --env-file .env python scripts/verify_monthly_summary.py
```

Initial loaders intentionally reject non-empty target tables.
The summary is a view, so its query uses the current staging data.

## Data Quality Findings

- Order IDs and customer IDs were populated and unique.
- All item composite keys were populated and unique.
- All checked order/customer references were found.
- There were 775 orders without items, including one shipped order.
- All delivered orders had items.
- All inspected item prices were finite and positive.

The cause of the shipped order without items has not been established.

## Limitations

- Historical data and manual execution.
- Initial loading only; incremental loading is not implemented.
- No scheduling, dashboard, or cloud deployment.
- Freight values and product/seller references were not validated.
- Fresh-clone reproduction is pending verification.

## Documentation

- [Project brief](project-brief.md)
- [Orders profiling](docs/orders-profiling.md)
- [Customers profiling](docs/customers-profiling.md)
- [Order items profiling](docs/order-items-profiling.md)
- [V1 validation results](docs/v1-validation.md)
