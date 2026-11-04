# Load or verify the order items snapshot using the shared loader.

import argparse
from pathlib import Path

from snapshot_loader import load_snapshot

project_root = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser(description="Load or verify order item data.")
parser.add_argument(
    "--input",
    type=Path,
    default=project_root / "data" / "raw" / "olist_order_items_dataset.csv",
)
args = parser.parse_args()

result = load_snapshot(
    table_name="order_items",
    file_path=args.input,
    expected_columns=[
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    key_columns=["order_id", "order_item_id"],
)

print(f"Order items load status: {result['status']}")
print(f"CSV rows: {result['source_rows']}")
print(f"Database rows: {result['database_rows']}")