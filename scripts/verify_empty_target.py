# Verify initial loading and rerunning using an isolated test table.

from pathlib import Path
from uuid import uuid4

from psycopg import sql

from snapshot_loader import get_connection, load_snapshot

project_root = Path(__file__).resolve().parent.parent
table_name = f"validation_customers_{uuid4().hex}"
test_table = sql.Identifier("staging", table_name)
table_created = False

options = {
    "table_name": table_name,
    "file_path": (
        project_root / "data" / "raw" / "olist_customers_dataset.csv"
    ),
    "expected_columns": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "key_columns": ["customer_id"],
}

try:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "CREATE TABLE {} "
                    "(LIKE staging.customers INCLUDING ALL);"
                ).format(test_table)
            )

    table_created = True

    initial_result = load_snapshot(**options)

    if initial_result["status"] != "loaded":
        raise RuntimeError("Expected loaded status for the empty target.")

    rerun_result = load_snapshot(**options)

    if rerun_result["status"] != "skipped":
        raise RuntimeError("Expected skipped status for matching data.")

    print("Empty-target load and rerun passed.")
    print(f"Initial status: {initial_result['status']}")
    print(f"Rerun status: {rerun_result['status']}")
    print(f"CSV rows: {initial_result['source_rows']}")
    print(f"Database rows: {rerun_result['database_rows']}")

finally:
    if table_created:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP TABLE {};").format(test_table)
                )

        print("Test table removed.")