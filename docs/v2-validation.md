# V2 Validation — Snapshot Loaders

## Scope
Safe reruns for `staging.customers` and `staging.orders`.
Customers currently uses its standalone implementation; orders uses the shared
`scripts/snapshot_loader.py` implementation.
Order items still uses its V1 initial-load behavior.

## Implemented Policy
- Empty target: load incoming data.
- Populated target with matching data: skip.
- Populated target with different data: reject the input.
- Compare complete rows in both directions using EXCEPT ALL.
- Preserve existing target rows when differing input is rejected.

## Executed Checks

### Customers: Changed Input
- Test CSV rows: 99,441.
- Customer IDs were preserved.
- One customer city changed from `franca` to `franca__v2_changed__`.
- The loader rejected the input with the expected RuntimeError.

### Customers: Original Input After Rejection
- Loader status: skipped.
- CSV rows: 99,441.
- Database rows: 99,441.
- The original CSV still matched the complete target table.

### Orders: Matching Input Before Rejection
- Loader status: skipped.
- CSV rows: 99,441.
- Database rows: 99,441.

### Orders: Changed Input
- Test CSV rows: 99,441.
- Order IDs and row count were preserved.
- One order status changed from `delivered` to `canceled`.
- The loader rejected the input with the expected RuntimeError:
  `staging.orders source differs from existing data. Load stopped; existing rows were preserved.`

### Orders: Original Input After Rejection
- Loader status: skipped.
- CSV rows: 99,441.
- Database rows: 99,441.
- The complete target table still matched the original CSV after rejection.

These runtime checks were executed manually by the learner and reviewed from
terminal screenshots. Matching is based on complete typed rows, not only counts.

## Test Files
- Customers generator: `scripts/create_customers_test_case.py`.
- Customers CSV: `data/raw/test_cases/customers_changed.csv`.
- Orders generator: `scripts/create_orders_test_case.py`.
- Orders CSV: `data/raw/test_cases/orders_changed.csv`.
- Generated CSV files are excluded from Git.

## Remaining Verification
- Initial loading into an empty table using the updated V2 loader.
- Additional invalid-input cases.

## Remaining Implementation
- Migrate customers to the shared snapshot loader.
- Extend safe rerun support to order items using the shared loader.
- Incremental loading and updates to existing target rows are not implemented.
