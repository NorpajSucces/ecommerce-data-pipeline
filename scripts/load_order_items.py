# Load the order items CSV into an empty staging table.

import csv
import os
from pathlib import Path

import psycopg

project_root = Path(__file__).resolve().parent.parent
file_path = project_root / "data" / "raw" / "olist_order_items_dataset.csv"

expected_columns = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value",
]

required_variables = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
]

missing_variables = [
    name
    for name in required_variables
    if not os.environ.get(name)
]

if missing_variables:
    raise ValueError(
        "Missing required environment variables: "
        + ", ".join(missing_variables)
    )

source_row_count = 0

with psycopg.connect(
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ["POSTGRES_PORT"]),
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    connect_timeout=10,
) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM staging.order_items;")
        existing_row_count = cursor.fetchone()[0]

        if existing_row_count > 0:
            raise RuntimeError(
                "staging.order_items is not empty. Initial load stopped."
            )

        with file_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames != expected_columns:
                raise ValueError(
                    "Order items CSV columns do not match the expected header."
                )

            with cursor.copy(
                """
                COPY staging.order_items (
                    order_id,
                    order_item_id,
                    product_id,
                    seller_id,
                    shipping_limit_date,
                    price,
                    freight_value
                )
                FROM STDIN
                """
            ) as copy:
                for row in reader:
                    source_row_count += 1

                    if None in row or any(
                        value is None for value in row.values()
                    ):
                        raise ValueError(
                            f"Malformed CSV record: {source_row_count}"
                        )

                    values = tuple(
                        None if row[column] == "" else row[column]
                        for column in expected_columns
                    )
                    copy.write_row(values)

        if source_row_count == 0:
            raise ValueError("Order items CSV has no data rows.")

        cursor.execute("SELECT COUNT(*) FROM staging.order_items;")
        database_row_count = cursor.fetchone()[0]

        if database_row_count != source_row_count:
            raise RuntimeError(
                "Row count mismatch between CSV and staging.order_items."
            )

print("Order items load completed.")
print(f"CSV rows: {source_row_count}")
print(f"Database rows: {database_row_count}")