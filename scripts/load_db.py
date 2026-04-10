import argparse
import csv
import sqlite3
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--csv-dir", default="data/csvs", help="Directory containing CSV exports")
parser.add_argument("--db", default="data/mindy_dataset.db", help="Output SQLite path")
args = parser.parse_args()

Path(args.db).parent.mkdir(parents=True, exist_ok=True)
Path(args.csv_dir).mkdir(parents=True, exist_ok=True)

TABLE_ORDER = [
    "airports",
    "airlines",
    "flights",
    "hotels",
    "hotel_availability",
    "activities",
]

conn = sqlite3.connect(args.db)

for table in TABLE_ORDER:
    csv_path = Path(args.csv_dir) / f"{table}.csv"
    if not csv_path.exists():
        print(f" {table}.csv not found")
        continue

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    if not rows:
        print(f"  {table}.csv empty ")
        continue

    conn.execute(f"DROP TABLE IF EXISTS {table}")

    col_types = []
    for i, col in enumerate(headers):
        sample = rows[0][i] if rows else ""
        try:
            int(sample)
            col_types.append("INTEGER")
        except ValueError:
            try:
                float(sample)
                col_types.append("REAL")
            except ValueError:
                col_types.append("TEXT")

    col_defs = ", ".join(f'"{h}" {t}' for h, t in zip(headers, col_types))
    conn.execute(f"CREATE TABLE {table} ({col_defs})")

    placeholders = ", ".join("?" * len(headers))
    conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    conn.commit()
    print(f"  {table:<25} {len(rows):>8,} rows")

indexes = [
    ("flights", "origin"),
    ("flights", "destination"),
    ("flights", "depart_date"),
    ("flights", "price"),
    ("hotels", "city"),
    ("hotels", "price_per_night"),
    ("hotel_availability", "hotel_id"),
    ("hotel_availability", "check_in"),
    ("activities", "city"),
    ("activities", "category"),
]

for table, col in indexes:
    try:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON {table}({col})")
        print(f"  idx_{table}_{col}")
    except Exception as e:
        print(f" fail for {table}.{col}: {e}")

conn.commit()
conn.close()