# Order Items Data Profiling

## Dataset Structure
- Total rows: 112,650.
- Total columns: 7.

## Composite Key Checks
- Candidate key: (`order_id`, `order_item_id`).
- Unique complete keys: 112,650.
- Rows with missing key components: 0.
- Rows with repeated composite key: 0.

## Order References
- Item rows with unmatched order ID: 0.
- Unique order IDs represented in items: 98,666.
- Orders without items: 775.
- Delivered orders without items: 0.

## Statuses of Orders Without Items
- unavailable: 603.
- canceled: 164.
- created: 5.
- invoiced: 2.
- shipped: 1.

The shipped order without items is a data consistency finding.
Its cause has not been established.

## Item Price Checks
- Rows with missing price: 0.
- Rows with invalid or non-finite price: 0.
- Rows with negative price: 0.
- Rows with zero price: 0.
- Rows with positive price: 112,650.

## Implications for V1
- Every delivered order has at least one item.
- All inspected item prices are finite and positive.
- Monthly analytics will include delivered orders.
- Total item value will exclude freight.
- Source rows will be preserved during ingestion.

## Scope Limitations
These checks do not establish that all source values are correct.
Freight values and references to products and sellers were not validated.