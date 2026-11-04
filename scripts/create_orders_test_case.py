# Create a changed orders CSV while preserving the original file.

import csv
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
source_path = project_root / "data" / "raw" / "olist_orders_dataset.csv"
target_path = (
    project_root / "data" / "raw" / "test_cases" / "orders_changed.csv"
)

with source_path.open(
    mode="r",
    encoding="utf-8-sig",
    newline="",
) as source_file:
    reader = csv.DictReader(source_file)
    fieldnames = reader.fieldnames
    first_row = next(reader, None)

    if first_row is None:
        raise ValueError("The source CSV has no data rows.")

    order_id = first_row["order_id"]
    original_status = first_row["order_status"]
    changed_status = (
        "canceled" if original_status == "delivered" else "delivered"
    )
    first_row["order_status"] = changed_status

    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open(
        mode="x",
        encoding="utf-8",
        newline="",
    ) as target_file:
        writer = csv.DictWriter(target_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(first_row)

        rows_written = 1

        for row in reader:
            writer.writerow(row)
            rows_written += 1

print(f"Test file: {target_path}")
print(f"Rows written: {rows_written}")
print(f"Order ID: {order_id}")
print(f"Original status: {original_status}")
print(f"Changed status: {changed_status}")