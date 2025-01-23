import csv
import gzip
import io
import requests

"""
Takes data from Neighborhood Association Boundaries data set on ChattaData: 
https://www.chattadata.org/Public-Safety/Neighborhood-Association-Boundaries/dxzz-idjy/data_preview

Strips the "description" field containing names of neighborhood association presidents and their contact info,
leaving only the name of the association and its boundaries.
"""

# Download public neighborhood association data from ChattaData as CSV
url = "https://www.chattadata.org/resource/dxzz-idjy.csv?$limit=10000000"
text = requests.get(url=url).text

# Get the data in the appropriate format for use
f = io.StringIO(text)
data = list(csv.DictReader(f))

# List of dictionaries, with each dictionary being a row of data to write
rows = []

for row in data:
    # Create the new row with only name and boundary
    row_data = {"name": row["name"], "boundary": row["boundary"]}
    rows.append(row_data)

# Write to csv.gz
with gzip.open("./geochatt/neighborhoods.csv.gz", "wt", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["name", "boundary"])
    writer.writeheader()
    writer.writerows(rows)