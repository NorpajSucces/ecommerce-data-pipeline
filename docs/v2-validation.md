# V2 Validation — Customers Loader

## Scope
Safe reruns for `staging.customers`.
Orders and order items still use their V1 initial-load behavior.

## Implemented Policy
- Empty target: load incoming data.
- Populated target with matching data: skip.
- Populated target with different data: reject the input.
- Compare complete rows in both directions using EXCEPT ALL.
- Preserve existing target rows when differing input is rejected.

## Executed Checks

### Changed Input
- Test CSV rows: 99,441.
- Customer IDs were preserved.
- One customer city changed from `franca` to `franca__v2_changed__`.
- The loader rejected the input with the expected RuntimeError.

### Original Input After Rejection
- Loader status: skipped.
- CSV rows: 99,441.
- Database rows: 99,441.
- The original CSV still matched the complete target table.

## Test Files
- Generator: `scripts/create_customers_test_case.py`.
- Generated CSV: `data/raw/test_cases/customers_changed.csv`.
- The generated CSV is excluded from Git.

## Remaining Verification
- Initial loading into an empty table using the updated V2 loader.
- Additional invalid-input cases.

## Remaining Implementation
- Extend safe rerun support to orders and order items.