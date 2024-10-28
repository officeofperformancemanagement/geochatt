import csv
import gzip
import json
import os
import zipfile

from shapely import from_wkt, STRtree
from shapely.geometry import shape, Point

csv.field_size_limit(10_000_000)

directory = os.path.dirname(os.path.realpath(__file__))

zipcode_shapes = []
with open(os.path.join(directory, "zipcodes.geojson")) as f:
    for feature in json.load(f)["features"]:
        zipcode_shapes.append(
            (shape(feature["geometry"]), int(feature["properties"]["zip_code"]))
        )

municipality_shapes = []
with open(os.path.join(directory, "municipalities.geojson")) as f:
    for feature in json.load(f)["features"]:
        municipality_shapes.append(
            (shape(feature["geometry"]), feature["properties"]["NAME"])
        )

city_council_districts_shapes = []
with open(os.path.join(directory, "city_council_districts.geojson")) as f:
    for feature in json.load(f)["features"]:
        city_council_districts_shapes.append(
            (shape(feature["geometry"]), int(float(feature["properties"]["citydst"])))
        )


def _get_shape_(shapes, longitude, latitude):
    point = Point(longitude, latitude)
    for shape, value in shapes:
        if shape.contains(point):
            return value


def get_city_council_district(longitude, latitude):
    return _get_shape_(city_council_districts_shapes, longitude, latitude)


def get_municipality(longitude, latitude):
    return _get_shape_(municipality_shapes, longitude, latitude)


def get_zipcode(longitude, latitude):
    return _get_shape_(zipcode_shapes, longitude, latitude)


parcel_strtree = {"value": None, "geoms": {}}


def get_address(longitude, latitude, max_distance=0.0001):
    # load address index the first time you call this method
    if parcel_strtree["value"] is None:
        with gzip.open(
            os.path.join(directory, "live_parcels.csv.gz"), "rt", newline=""
        ) as f:
            for row in csv.DictReader(f):
                geom = from_wkt(row["geometry"])
                if row["ADDRESS"]:
                    parcel_strtree["geoms"][geom] = row["ADDRESS"]
            parcel_strtree["value"] = STRtree(
                [geom for geom, address in parcel_strtree["geoms"].items()]
            )

    point = Point(longitude, latitude)
    index = parcel_strtree["value"].nearest(point)
    nearest_geom = parcel_strtree["value"].geometries.take(index)
    if point.distance(nearest_geom) <= max_distance:
        return parcel_strtree["geoms"][nearest_geom]
