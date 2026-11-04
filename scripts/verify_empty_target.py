# Verify initial loading and reruns with isolated related tables.

from pathlib import Path
from uuid import uuid4

from psycopg import sql

from snapshot_loader import get_connection, load_snapshot

project_root = Path(__file__).resolve().parent.parent
run_id = uuid4().hex
tables_created = False

datasets = [
    (
        "customers",
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
        ["customer_id"],
    ),
    (
        "orders",
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        ["order_id"],
    ),
    (
        "order_items",
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
        ["order_id", "order_item_id"],
    ),
]

table_names = {
    name: f"validation_{name}_{run_id}"
    for name, _, _ in datasets
}

relationships = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
]


def test_table(name):
    return sql.Identifier("staging", table_names[name])


try:
    # Create all test tables and relationships in one transaction.
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for name, _, _ in datasets:
                cursor.execute(
                    sql.SQL(
                        "CREATE TABLE {} "
                        "(LIKE {} INCLUDING ALL);"
                    ).format(
                        test_table(name),
                        sql.Identifier("staging", name),
                    )
                )

            for child, child_column, parent, parent_column in relationships:
                cursor.execute(
                    sql.SQL(
                        "ALTER TABLE {} "
                        "ADD FOREIGN KEY ({}) REFERENCES {} ({});"
                    ).format(
                        test_table(child),
                        sql.Identifier(child_column),
                        test_table(parent),
                        sql.Identifier(parent_column),
                    )
                )

    tables_created = True

    # First load all datasets, then verify matching reruns.
    for expected_status in ("loaded", "skipped"):
        print(f"Checking {expected_status}...", flush=True)

        for name, columns, keys in datasets:
            result = load_snapshot(
                table_name=table_names[name],
                file_path=(
                    project_root
                    / "data"
                    / "raw"
                    / f"olist_{name}_dataset.csv"
                ),
                expected_columns=columns,
                key_columns=keys,
            )

            if result["status"] != expected_status:
                raise RuntimeError(
                    f"{name}: expected {expected_status}, "
                    f"got {result['status']}."
                )

            print(
                f"{name}: {result['status']} | "
                f"CSV rows: {result['source_rows']} | "
                f"Database rows: {result['database_rows']}",
                flush=True,
            )

finally:
    if tables_created:
        # Remove child tables before their referenced parent tables.
        with get_connection() as connection:
            with connection.cursor() as cursor:
                for name, _, _ in reversed(datasets):
                    cursor.execute(
                        sql.SQL("DROP TABLE {};").format(
                            test_table(name)
                        )
                    )

        print("Test tables removed.", flush=True)

print("Empty-target dependency check passed.")