# Read the orders CSV and profile IDs, statuses, and purchase timestamps.

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
file_path = project_root / "data" / "raw" / "olist_orders_dataset.csv"

with file_path.open(mode="r", encoding="utf-8-sig", newline="") as csv_file:
    reader = csv.DictReader(csv_file)

    columns = reader.fieldnames
    row_count = 0

    seen_order_ids = set()
    missing_order_ids_rows = 0
    duplicate_order_ids_rows = 0

    status_counts = Counter()

    missing_purchase_timestamps_rows = 0
    purchase_timestamp_sample = []

    valid_purchase_timestamp_rows = 0
    invalid_purchase_timestamp_rows = 0
    invalid_purchase_timestamp_samples = []

    for row in reader:
        row_count += 1

        order_id = row["order_id"].strip()
        order_status = row["order_status"].strip()
        purchase_timestamp = row["order_purchase_timestamp"].strip()

        # Check order IDs.
        if not order_id:
            missing_order_ids_rows += 1
        elif order_id in seen_order_ids:
            duplicate_order_ids_rows += 1
        else:
            seen_order_ids.add(order_id)

        # Count order statuses.
        status_counts[order_status or "<missing>"] += 1

        # Check and validate purchase timestamps.
        if not purchase_timestamp:
            missing_purchase_timestamps_rows += 1
        else:
            if len(purchase_timestamp_sample) < 5:
                purchase_timestamp_sample.append(purchase_timestamp)

            try:
                datetime.strptime(
                    purchase_timestamp,
                    "%Y-%m-%d %H:%M:%S",
                )
            except ValueError:
                invalid_purchase_timestamp_rows += 1

                if len(invalid_purchase_timestamp_samples) < 5:
                    invalid_purchase_timestamp_samples.append(
                        (order_id, purchase_timestamp)
                    )
            else:
                valid_purchase_timestamp_rows += 1

print(f"File: {file_path.name}")
print(f"Rows: {row_count}")
print("Columns:")

for column in columns:
    print(f"- {column}")

print()
print("Order ID checks:")
print(f"Unique non-empty order IDs: {len(seen_order_ids)}")
print(f"Rows with missing order ID: {missing_order_ids_rows}")
print(f"Rows with repeated order ID: {duplicate_order_ids_rows}")

print()
print("Order status counts:")

for status, count in status_counts.most_common():
    print(f"- {status}: {count}")

print()
print("Purchase timestamp checks:")
print(f"Rows with missing purchase timestamp: {missing_purchase_timestamps_rows}")

print("Sample purchase timestamps:")

for timestamp in purchase_timestamp_sample:
    print(f"- {timestamp}")

print()
print("Purchase timestamp validation:")
print(f"Valid timestamps: {valid_purchase_timestamp_rows}")
print(f"Invalid non-empty timestamps: {invalid_purchase_timestamp_rows}")

for order_id, timestamp in invalid_purchase_timestamp_samples:
    print(f"- Order {order_id}: {timestamp}")