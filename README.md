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

## Analytical Rules

- Include orders with status `delivered` in the dataset snapshot.
- Group orders by purchase month using `order_purchase_timestamp`.
- Sum item prices, excluding freight.
- Aggregate items per order before counting orders.
- Omit months without delivered orders.
- Preserve all source order statuses in staging.

Output: `analytics.monthly_order_summary`.

| Column | Meaning |
|---|---|
| `order_month` | First day of the purchase month |
| `order_count` | Number of delivered orders purchased that month |
| `total_item_value` | Total item prices for those orders, excluding freight |

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