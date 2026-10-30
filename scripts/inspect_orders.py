# file → buka CSV → baca header → hitung baris data → tampilkan hasil
import csv
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
file_path = project_root / "data" / "raw" / "olist_orders_dataset.csv"

with file_path.open(mode="r", encoding="utf-8-sig", newline="") as csv_file:
    reader = csv.DictReader(csv_file)

    columns = reader.fieldnames
    row_count = sum(1 for row in reader)

print(f"File: {file_path.name}")
print(f"Rows: {row_count}")
print("Columns:")

for column in columns:
    print(f"- {column}")