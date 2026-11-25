# V2 Validation — Snapshot Loaders

## Scope
Safe reruns for `staging.customers`, `staging.orders`, and `staging.order_items`.
All three loaders now use the shared `scripts/snapshot_loader.py`
implementation. Customer checks cover both the previous standalone implementation
and the shared implementation after migration.
Matching-input reruns and changed-input rejection have been checked for all three
datasets, including original-input reruns after rejection.
The sequential runner is implemented in `scripts/run_pipeline.py` for an
existing setup with staging tables and the monthly summary view.
The audited runner additionally requires `audit.pipeline_runs`, created by
`sql/003_create_pipeline_audit.sql`.

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

### Empty Target: Isolated Customers Table (Earlier Script Version)
- Ran `uv run --env-file .env python scripts/verify_empty_target.py`.
- The learner reported the expected output in chat without a terminal screenshot.
- The script created a uniquely named table in `staging` using
  `LIKE staging.customers INCLUDING ALL`.
- Initial status: loaded; CSV rows: 99,441.
- Rerun status: skipped; database rows: 99,441.
- The rerun used a new connection and confirmed the committed rows matched the source.
- The script reported `Test table removed.` after cleanup.
- This checks the shared initial-load path with the customers structure; it does
  not verify initial loading of the orders/items foreign-key dependency chain.

### Empty Targets: All Datasets with Foreign Keys
- Ran the expanded `scripts/verify_empty_target.py` using the original CSV files.
- Three uniquely named tables were created with the staging table structures.
- Foreign keys explicitly linked test orders to test customers and test items
  to test orders before loading began.
- Initial loading ran in customers, orders, order items order.

| Dataset | Initial status | Rerun status | CSV and database rows |
|---|---|---|---|
| Customers | loaded | skipped | 99,441 |
| Orders | loaded | skipped | 99,441 |
| Order items | loaded | skipped | 112,650 |

- Each loader call used its own connection and transaction. The second pass
  compared committed target rows with the original CSVs.
- Cleanup ran in reverse dependency order.
- Final messages: `Test tables removed.` and
  `Empty-target dependency check passed.`
- All six load/rerun results and cleanup messages were reviewed from a terminal
  screenshot supplied by the learner.
- This verifies successful loading with foreign keys active. Deliberate invalid
  foreign-key rejection and fresh-clone setup were not tested by this script.

### Monthly Summary After Shared Loader Migration
- Ran `uv run --env-file .env python scripts/verify_monthly_summary.py`.
- Result: `Monthly reconciliation passed.`
- Months checked: 23.
- Delivered orders: 96,478.
- Total item value: 13,221,498.11 (excluding freight).
- The script compared month coverage, order counts, and item values for each month
  against independent calculations from the original CSV files.
- The result was reviewed from a terminal screenshot.

### Sequential Runner: Successful Rerun
- Ran `uv run --env-file .env python scripts/run_pipeline.py`.
- Database connection check passed.
- Customers: skipped; CSV and database rows both 99,441.
- Orders: skipped; CSV and database rows both 99,441.
- Order items: skipped; CSV and database rows both 112,650.
- Monthly reconciliation passed: 23 months, 96,478 delivered orders, and
  total item value 13,221,498.11.
- Final message: `Pipeline completed successfully.`
- All five stages and the final message were reviewed from a terminal screenshot.
- This verifies the successful rerun path. Simulated failure handling is checked
  separately below.

### Sequential Runner: Simulated Orders Failure
- Test: `tests/test_run_pipeline.py`.
- Initial execution by the assistant before the directory rename: 1 test passed (`OK`).
- After renaming the directory to `tests`, the learner reported the same successful
  result with `uv run python -m unittest discover -s tests -v`.
- Subprocess calls were mocked: the first two succeeded and orders raised
  `CalledProcessError` with exit code 7.
- Only connection, customers, and orders were called, in that order.
- The runner raised `SystemExit(7)` and reported the failed orders stage.
- The success message was absent.
- This checks control flow under a simulated subprocess failure; it does not
  exercise an actual loader/database failure.

### Pipeline Audit: Successful Run
- Reviewed from a pgAdmin screenshot supplied by the learner (`run_id`: `d55c9187-b569-4d69-a076-a10ffa5885da`).
- Start and finish timestamps were populated, with duration approximately 26 seconds.
- Final result: succeeded; failed step: NULL; exit code: 0.
- The helper inserts a running row before the pipeline steps and finalizes it
  using a separate transaction.

### Pipeline Audit: Failed Run and Subsequent Succeeded Rerun (PostgreSQL)
- Updated `sql/003_create_pipeline_audit.sql` to enforce full state consistency across
  `status`, `finished_at`, `failed_step`, and `exit_code` via `pipeline_runs_finish_state_check`,
  and applied it cleanly to PostgreSQL with existing rows intact.
- Ran `uv run --env-file .env python scripts/run_pipeline.py --orders-input data/raw/test_cases/orders_changed.csv`.
  - `run_id`: `7f49ad18-1c4b-4889-b6c1-47a16ea96e79`.
  - Connection check passed and customers was skipped (99,441 rows).
  - Step 3 (`Load or verify orders`) rejected the changed input with `RuntimeError`
    while preserving existing rows in `staging.orders`, stopping the runner with exit code 1.
  - Persisted row verified in `audit.pipeline_runs`: `status = failed`,
    `failed_step = 'Load or verify orders'`, `exit_code = 1`, duration ~15.65 seconds.
- Ran `uv run --env-file .env python scripts/run_pipeline.py` with the original CSVs.
  - `run_id`: `961b8363-1d10-467e-9504-102eaa87e820`.
  - All three loaders reported `skipped` (confirming `staging` data was unchanged) and
    monthly reconciliation passed (23 months, 96,478 delivered orders, `13221498.11`).
  - Persisted row verified in `audit.pipeline_runs`: `status = succeeded`,
    `failed_step = NULL`, `exit_code = 0`, duration ~26.79 seconds.

### Pipeline Audit and Runner Unit Tests (Offline)
- Expanded tests in `tests/test_run_pipeline.py` and added `tests/test_pipeline_audit.py`.
- Executed `uv run python -m unittest discover -s tests -v`.
- Result: 12 tests passed (`OK`), covering happy path, orders failure, audit start failure,
  audit finish failure, keyboard interrupt (`exit_code = 130`), CLI input overrides,
  and audit helper input/rowcount validation.
- No PostgreSQL connection was made by these tests.

Runtime checks were executed against local PostgreSQL; evidence is recorded above.
Matching is based on complete typed rows (explicit column list via `EXCEPT ALL`), not only counts.

## Test Files
- Customers generator: `scripts/create_customers_test_case.py`.
- Customers CSV: `data/raw/test_cases/customers_changed.csv`.
- Orders generator: `scripts/create_orders_test_case.py`.
- Orders CSV: `data/raw/test_cases/orders_changed.csv`.
- Order items generator: `scripts/create_order_items_test_case.py`.
- Order items CSV: `data/raw/test_cases/order_items_changed.csv`.
- Empty-target integration check: `scripts/verify_empty_target.py`.
- Runner control-flow tests: `tests/test_run_pipeline.py`.
- Audit helper unit tests: `tests/test_pipeline_audit.py`.
- Generated CSV files are excluded from Git.

## Remaining Verification
- Additional invalid-input cases.
- Fresh-clone setup reproduction.

## Remaining Implementation
- Incremental loading and updates to existing target rows are not implemented.
