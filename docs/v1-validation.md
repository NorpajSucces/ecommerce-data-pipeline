# V1 Validation Results

## Source-to-Database Row Counts
- Customers: 99,441 CSV rows matched 99,441 database rows.
- Orders: 99,441 CSV rows matched 99,441 database rows.
- Order items: 112,650 CSV rows matched 112,650 database rows.
- Order items represent 98,666 distinct orders.
- Database counts were checked through separate connections.

## Monthly Summary
- View: `analytics.monthly_order_summary`.
- Included order status: `delivered`.
- Month definition: purchase month.
- Metric: total item value, excluding freight.

## Independent CSV Reconciliation
- Result: passed.
- Months checked: 23.
- Delivered orders: 96,478.
- Total item value: 13221498.11.
- Month coverage, order counts, and item values matched
  between the source CSV calculation and the SQL view.

## Current Limitations
- The pipeline processes a historical dataset manually.
- Loaders support initial loading and reject non-empty target tables.
- Incremental loading and scheduling are not implemented.
- Reproduction from a fresh clone has not yet been verified.