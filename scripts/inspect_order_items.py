# Inspect the structure and sample rows of the order items dataset.

import csv
from pathlib import Path
from collections import Counter
from decimal import Decimal, InvalidOperation

project_root = Path(__file__).resolve().parent.parent
file_path = project_root / "data" / "raw" / "olist_order_items_dataset.csv"

row_count = 0
sample_rows = []
seen_item_keys = set()
missing_item_key_rows = 0
duplicate_item_key_rows = 0
orders_path = project_root / "data" / "raw" / "olist_orders_dataset.csv"

known_order_ids = set()
delivered_order_ids = set()
order_status_by_id = {}

with orders_path.open(
    mode="r",
    encoding="utf-8-sig",
    newline="",
) as orders_file:
    orders_reader = csv.DictReader(orders_file)

    for order in orders_reader:
        source_order_id = order["order_id"].strip()
        source_order_status = order["order_status"].strip()

        if source_order_id:
            known_order_ids.add(source_order_id)
            order_status_by_id[source_order_id] = source_order_status or "<missing>"

            if source_order_status == "delivered":
                delivered_order_ids.add(source_order_id)

item_order_ids = set()
unmatched_order_reference_rows = 0
missing_price_rows = 0
invalid_price_rows = 0
negative_price_rows = 0
zero_price_rows = 0
positive_price_rows = 0

with file_path.open(
    mode="r",
    encoding="utf-8-sig",
    newline="",
) as csv_file:
    reader = csv.DictReader(csv_file)
    columns = reader.fieldnames

    for row in reader:
        row_count += 1
        order_id = row["order_id"].strip()
        order_item_id = row["order_item_id"].strip()
        price_text = row["price"].strip()

        if not price_text:
            missing_price_rows += 1
        else:
            try:
                price = Decimal(price_text)
            except InvalidOperation:
                invalid_price_rows += 1
            else:
                if not price.is_finite():
                    invalid_price_rows += 1
                elif price < 0:
                    negative_price_rows += 1
                elif price == 0:
                    zero_price_rows += 1
                else:
                    positive_price_rows += 1

        if order_id:
            item_order_ids.add(order_id)

            if order_id not in known_order_ids:
                unmatched_order_reference_rows += 1

        if not order_id or not order_item_id:
            missing_item_key_rows += 1

        else:
            item_key = (order_id, order_item_id)

            if item_key in seen_item_keys:
                duplicate_item_key_rows += 1
            else:
                seen_item_keys.add(item_key)

        if len(sample_rows) < 3:
            sample_rows.append(row)

print(f"File: {file_path.name}")
print(f"Rows: {row_count}")

print()
print("Columns:")

for column in columns:
    print(f"- {column}")

print()
print("Sample rows:")

for sample_number, sample in enumerate(sample_rows, start=1):
    print(f"Sample {sample_number}:")

    for column, value in sample.items():
        print(f"  {column}: {value}")

    print()

print()
print("Order item key checks:")
print(f"Unique complete item keys: {len(seen_item_keys)}")
print(f"Rows with missing key components: {missing_item_key_rows}")
print(f"Rows with repeated item key: {duplicate_item_key_rows}")

orders_without_items = known_order_ids - item_order_ids
delivered_orders_without_items = delivered_order_ids - item_order_ids

print()
print("Order reference checks:")
print(f"Item rows with unmatched order ID: {unmatched_order_reference_rows}")
print(f"Unique order IDs represented in items: {len(item_order_ids)}")
print(f"Orders without items: {len(orders_without_items)}")
print(f"Delivered orders without items: {len(delivered_orders_without_items)}")

orders_without_items_status_counts = Counter(
    order_status_by_id[order_id]
    for order_id in orders_without_items
)

print()
print("Statuses of orders without items:")

for status, count in orders_without_items_status_counts.most_common():
    print(f"- {status}: {count}")

print()
print("Item price checks:")
print(f"Rows with missing price: {missing_price_rows}")
print(f"Rows with invalid or non-finite price: {invalid_price_rows}")
print(f"Rows with negative price: {negative_price_rows}")
print(f"Rows with zero price: {zero_price_rows}")
print(f"Rows with positive price: {positive_price_rows}")