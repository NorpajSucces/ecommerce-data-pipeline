# Load or verify the customers snapshot using the shared loader.

import argparse
from pathlib import Path

from snapshot_loader import load_snapshot

project_root = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser(description="Load or verify customer data.")
parser.add_argument(
    "--input",
    type=Path,
    default=project_root / "data" / "raw" / "olist_customers_dataset.csv",
)
args = parser.parse_args()

result = load_snapshot(
    table_name="customers",
    file_path=args.input,
    expected_columns=[
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    key_columns=["customer_id"],
)

print(f"Customers load status: {result['status']}")
print(f"CSV rows: {result['source_rows']}")
print(f"Database rows: {result['database_rows']}")
