import csv
import gzip
import io
import json
import math
import requests

csv.field_size_limit(2147483647)  # maximum value of a long

data = requests.get(
    "https://raw.githubusercontent.com/officeofperformancemanagement/live-parcels/refs/heads/main/live_parcels.csv.gz"
).content

text = gzip.decompress(data).decode("utf-8")

rows = list(csv.DictReader(io.StringIO(text)))

rows = [
    {"ADDRESS": row["ADDRESS"], "geometry": row["geometry"]}
    for row in rows
    if row["ADDRESS"]
]

with gzip.open("./geochatt/live_parcels.csv.gz", "wt", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["ADDRESS", "geometry"])
    writer.writeheader()
    writer.writerows(rows)
