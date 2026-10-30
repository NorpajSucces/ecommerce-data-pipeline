# Orders Data Profiling

## Verified Findings
- Total rows: 99,441.
- Unique non-empty order IDs: 99,441.
- Rows with missing order ID: 0.
- Rows with repeated order ID: 0.
- Delivered orders: 96,478.
- Status counts sum to the total row count.
- No empty order status was reported.

## Proposed V1 Rules
- Include delivered orders.
- Group orders by purchase month.
- Calculate total item value excluding freight.

## Remaining Checks
- Validate purchase timestamps.
- Check customer references.
- Check relationships between orders and order items.
- Validate item prices before aggregation.