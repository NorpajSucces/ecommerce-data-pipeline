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

## Purchase Timestamp Validation
- Checked column: `order_purchase_timestamp`.
- Parsing format: `%Y-%m-%d %H:%M:%S`.
- Rows with missing purchase timestamp: 0.
- Rows with successfully parsed purchase timestamp: 99,441.
- Rows with invalid non-empty purchase timestamp: 0.
- All rows have a populated and parseable purchase timestamp.