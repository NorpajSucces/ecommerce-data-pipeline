# Load or verify the orders snapshot using the shared loader.

import argparse
from pathlib import Path

from snapshot_loader import load_snapshot

project_root = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser(description="Load or verify order data.")
parser.add_argument(
    "--input",
    type=Path,
    default=project_root / "data" / "raw" / "olist_orders_dataset.csv",
)
args = parser.parse_args()

result = load_snapshot(
    table_name="orders",
    file_path=args.input,
    expected_columns=[
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    key_columns=["order_id"],
)

print(f"Orders load status: {result['status']}")
print(f"CSV rows: {result['source_rows']}")
print(f"Database rows: {result['database_rows']}")
