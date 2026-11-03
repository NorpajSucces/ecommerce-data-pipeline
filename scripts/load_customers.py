# Load customers initially or skip when all source rows already match.

import argparse
import csv
import os
from pathlib import Path

import psycopg

project_root = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser(description="Load or verify customer data.")
parser.add_argument(
    "--input",
    type=Path,
    default=project_root / "data" / "raw" / "olist_customers_dataset.csv",
)
args = parser.parse_args()
file_path = args.input

expected_columns = [
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
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
        # Prevent concurrent writes while deciding whether to load or skip.
        cursor.execute("SET LOCAL lock_timeout = '10s';")
        cursor.execute(
            "LOCK TABLE staging.customers IN SHARE ROW EXCLUSIVE MODE;"
        )

        # Validate incoming rows using the same structure and primary key.
        cursor.execute(
            """
            CREATE TEMP TABLE incoming_customers
            (LIKE staging.customers INCLUDING ALL)
            ON COMMIT DROP;
            """
        )

        with file_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames != expected_columns:
                raise ValueError(
                    "Customers CSV columns do not match the expected header."
                )

            with cursor.copy(
                """
                COPY incoming_customers (
                    customer_id,
                    customer_unique_id,
                    customer_zip_code_prefix,
                    customer_city,
                    customer_state
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

                    if not row["customer_id"].strip():
                        raise ValueError(
                            f"Missing customer_id at record {source_row_count}"
                        )

                    values = tuple(
                        None if row[column] == "" else row[column]
                        for column in expected_columns
                    )
                    copy.write_row(values)

        if source_row_count == 0:
            raise ValueError("Customers CSV has no data rows.")

        cursor.execute("SELECT COUNT(*) FROM staging.customers;")
        existing_row_count = cursor.fetchone()[0]

        if existing_row_count == 0:
            cursor.execute(
                """
                INSERT INTO staging.customers (
                    customer_id,
                    customer_unique_id,
                    customer_zip_code_prefix,
                    customer_city,
                    customer_state
                )
                SELECT
                    customer_id,
                    customer_unique_id,
                    customer_zip_code_prefix,
                    customer_city,
                    customer_state
                FROM incoming_customers;
                """
            )
            load_status = "loaded"
        else:
            # Compare complete rows in both directions, including multiplicity.
            cursor.execute(
                """
                SELECT EXISTS (
                    (
                        SELECT * FROM incoming_customers
                        EXCEPT ALL
                        SELECT * FROM staging.customers
                    )
                    UNION ALL
                    (
                        SELECT * FROM staging.customers
                        EXCEPT ALL
                        SELECT * FROM incoming_customers
                    )
                );
                """
            )
            data_differs = cursor.fetchone()[0]

            if data_differs:
                raise RuntimeError(
                    "Customers source differs from existing data. "
                    "Load stopped; existing rows were preserved."
                )

            load_status = "skipped"

        cursor.execute("SELECT COUNT(*) FROM staging.customers;")
        database_row_count = cursor.fetchone()[0]

        if database_row_count != source_row_count:
            raise RuntimeError(
                "Row count mismatch between CSV and staging.customers."
            )

print(f"Customers load status: {load_status}")
print(f"CSV rows: {source_row_count}")
print(f"Database rows: {database_row_count}")