# file → buka CSV → baca header → hitung baris data → tampilkan hasil
import csv
from pathlib import Path
from collections import Counter

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

    for row in reader:
        row_count += 1

        order_id = row["order_id"].strip()
        order_status = row["order_status"].strip()

        if not order_id:
            missing_order_ids_rows += 1
        elif order_id in seen_order_ids:
            duplicate_order_ids_rows += 1
        else:
            seen_order_ids.add(order_id)
        status_counts[order_status or "<missing>"] += 1

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