# V2 Validation — Snapshot Loaders

## Scope
Safe reruns for `staging.customers`, `staging.orders`, and `staging.order_items`.
All three loaders now use the shared `scripts/snapshot_loader.py`
implementation. Customer checks cover both the previous standalone implementation
and the shared implementation after migration.
Matching-input reruns and changed-input rejection have been checked for all three
datasets, including original-input reruns after rejection.

## Implemented Policy
- Empty target: load incoming data.
- Populated target with matching data: skip.
- Populated target with different data: reject the input.
- Compare complete rows in both directions using EXCEPT ALL.
- Preserve existing target rows when differing input is rejected.

## Executed Checks

### Customers: Changed Input (Standalone Implementation)
- Test CSV rows: 99,441.
- Customer IDs were preserved.
- One customer city changed from `franca` to `franca__v2_changed__`.
- The loader rejected the input with the expected RuntimeError.

### Customers: Original Input After Rejection (Standalone Implementation)
- Loader status: skipped.
- CSV rows: 99,441.
- Database rows: 99,441.
- The original CSV still matched the complete target table.

### Customers: Shared Loader After Migration
- Original input before rejection: skipped; CSV and database rows both 99,441.
- The existing changed-city fixture was rejected with the expected RuntimeError:
  `staging.customers source differs from existing data. Load stopped; existing rows were preserved.`
- The traceback showed that `load_customers.py` called `snapshot_loader.py`.
- Original input after rejection: skipped; CSV and database rows both 99,441.
- Complete-row comparison confirmed the target still matched the original CSV.

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

### Order Items: Matching Input
- The learner reported the expected result after switching to the shared loader:
  skipped; CSV and database rows both 112,650.
- This result was reported in chat without a terminal screenshot.

### Order Items: Changed Input
- Test CSV rows: 112,650; item keys were preserved.
- One item price changed from `58.90` to `58.91`.
- The loader rejected the input with the expected RuntimeError:
  `staging.order_items source differs from existing data. Load stopped; existing rows were preserved.`
- The traceback showed that `load_order_items.py` called `snapshot_loader.py`.

### Order Items: Original Input After Rejection
- Loader status: skipped.
- CSV rows: 112,650.
- Database rows: 112,650.
- Complete-row comparison confirmed the target still matched the original CSV.
- Changed-input rejection and the subsequent original-input rerun were reviewed
  from a terminal screenshot.

### Monthly Summary After Shared Loader Migration
- Ran `uv run --env-file .env python scripts/verify_monthly_summary.py`.
- Result: `Monthly reconciliation passed.`
- Months checked: 23.
- Delivered orders: 96,478.
- Total item value: 13,221,498.11 (excluding freight).
- The script compared month coverage, order counts, and item values for each month
  against independent calculations from the original CSV files.
- The result was reviewed from a terminal screenshot.

Runtime checks were executed manually by the learner; evidence is identified above.
Matching is based on complete typed rows, not only counts.

## Test Files
- Customers generator: `scripts/create_customers_test_case.py`.
- Customers CSV: `data/raw/test_cases/customers_changed.csv`.
- Orders generator: `scripts/create_orders_test_case.py`.
- Orders CSV: `data/raw/test_cases/orders_changed.csv`.
- Order items generator: `scripts/create_order_items_test_case.py`.
- Order items CSV: `data/raw/test_cases/order_items_changed.csv`.
- Generated CSV files are excluded from Git.

## Remaining Verification
- Initial loading into an empty table using the updated V2 loader.
- Additional invalid-input cases.

## Remaining Implementation
- Incremental loading and updates to existing target rows are not implemented.
