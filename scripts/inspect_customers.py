# Profile customer IDs and check customer references from orders.

import csv
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
raw_directory = project_root / "data" / "raw"

customers_path = raw_directory / "olist_customers_dataset.csv"
orders_path = raw_directory / "olist_orders_dataset.csv"

customer_row_count = 0
customer_ids = set()
missing_customer_id_rows = 0
duplicate_customer_id_rows = 0

# Collect customer IDs and check whether they are populated and unique.
with customers_path.open(
    mode="r",
    encoding="utf-8-sig",
    newline="",
) as csv_file:
    reader = csv.DictReader(csv_file)

    for row in reader:
        customer_row_count += 1
        customer_id = row["customer_id"].strip()

        if not customer_id:
            missing_customer_id_rows += 1
        elif customer_id in customer_ids:
            duplicate_customer_id_rows += 1
        else:
            customer_ids.add(customer_id)

order_row_count = 0
orders_missing_customer_id_rows = 0
orders_unmatched_customer_id_rows = 0
unmatched_customer_samples = []

# Check customer references across all order statuses.
with orders_path.open(
    mode="r",
    encoding="utf-8-sig",
    newline="",
) as csv_file:
    reader = csv.DictReader(csv_file)

    for row in reader:
        order_row_count += 1

        order_id = row["order_id"].strip()
        customer_id = row["customer_id"].strip()

        if not customer_id:
            orders_missing_customer_id_rows += 1
        elif customer_id not in customer_ids:
            orders_unmatched_customer_id_rows += 1

            if len(unmatched_customer_samples) < 5:
                unmatched_customer_samples.append(
                    (order_id, customer_id)
                )

print("Customers ID checks:")
print(f"Customer rows: {customer_row_count}")
print(f"Unique non-empty customer IDs: {len(customer_ids)}")
print(f"Rows with missing customer ID: {missing_customer_id_rows}")
print(f"Rows with repeated customer ID: {duplicate_customer_id_rows}")

print()
print("Customer references from orders:")
print(f"Order rows checked: {order_row_count}")
print(f"Orders with missing customer ID: {orders_missing_customer_id_rows}")
print(f"Orders with unmatched customer ID: {orders_unmatched_customer_id_rows}")

for order_id, customer_id in unmatched_customer_samples:
    print(f"- Order {order_id}: unmatched customer ID {customer_id}")