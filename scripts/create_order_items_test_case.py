# Create a changed item price CSV while preserving the original file.

import csv
from decimal import Decimal
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
source_path = project_root / "data" / "raw" / "olist_order_items_dataset.csv"
target_path = (
    project_root / "data" / "raw" / "test_cases" / "order_items_changed.csv"
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

    item_key = (first_row["order_id"], first_row["order_item_id"])
    original_price = Decimal(first_row["price"])
    changed_price = original_price + Decimal("0.01")
    first_row["price"] = str(changed_price)

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
print(f"Item key: {item_key}")
print(f"Original price: {original_price}")
print(f"Changed price: {changed_price}")