# Reconcile the monthly SQL summary against the source CSV files.

import csv
import os
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg

project_root = Path(__file__).resolve().parent.parent
raw_directory = project_root / "data" / "raw"

orders_path = raw_directory / "olist_orders_dataset.csv"
items_path = raw_directory / "olist_order_items_dataset.csv"

order_months = {}
expected_order_counts = Counter()
expected_item_values = defaultdict(lambda: Decimal("0"))

# Count delivered orders by purchase month directly from the orders CSV.
with orders_path.open(
    mode="r", encoding="utf-8-sig", newline=""
) as csv_file:
    for row in csv.DictReader(csv_file):
        if row["order_status"].strip() != "delivered":
            continue

        order_id = row["order_id"].strip()

        if not order_id or order_id in order_months:
            raise ValueError(
                "Missing or repeated delivered order ID in the source CSV."
            )

        purchase_date = datetime.strptime(
            row["order_purchase_timestamp"].strip(),
            "%Y-%m-%d %H:%M:%S",
        ).date()

        order_month = purchase_date.replace(day=1)
        order_months[order_id] = order_month
        expected_order_counts[order_month] += 1

if not order_months:
    raise ValueError("No delivered orders found in the source CSV.")

# Sum item prices directly into the corresponding purchase month.
with items_path.open(
    mode="r", encoding="utf-8-sig", newline=""
) as csv_file:
    for row in csv.DictReader(csv_file):
        order_id = row["order_id"].strip()

        if order_id not in order_months:
            continue

        price = Decimal(row["price"].strip())

        if not price.is_finite() or price <= 0:
            raise ValueError(
                f"Invalid item price for delivered order {order_id}."
            )

        order_month = order_months[order_id]
        expected_item_values[order_month] += price

expected_summary = {
    month: (count, expected_item_values[month])
    for month, count in expected_order_counts.items()
}

# Read the independently calculated SQL summary.
with psycopg.connect(
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ["POSTGRES_PORT"]),
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    connect_timeout=10,
) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT order_month, order_count, total_item_value
            FROM analytics.monthly_order_summary
            ORDER BY order_month;
            """
        )
        database_rows = cursor.fetchall()

actual_summary = {
    month: (count, item_value)
    for month, count, item_value in database_rows
}

if len(actual_summary) != len(database_rows):
    raise RuntimeError("The SQL summary contains repeated months.")

# Check month coverage, order counts, and exact decimal totals.
mismatch_count = 0

for month in sorted(set(expected_summary) | set(actual_summary)):
    expected = expected_summary.get(month)
    actual = actual_summary.get(month)

    if expected != actual:
        mismatch_count += 1
        print(f"Month: {month}")
        print(f"  CSV: {expected}")
        print(f"  Database: {actual}")

if mismatch_count:
    raise RuntimeError(
        f"Monthly reconciliation failed for {mismatch_count} month(s)."
    )

total_item_value = sum(expected_item_values.values(), Decimal("0"))

print("Monthly reconciliation passed.")
print(f"Months checked: {len(expected_summary)}")
print(f"Delivered orders: {sum(expected_order_counts.values())}")
print(f"Total item value: {total_item_value:.2f}")