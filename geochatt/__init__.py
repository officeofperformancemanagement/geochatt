import argparse
import csv
import gzip
import json
import os
import re
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


# Create Dict that has addresses as keys and parcels as values
parcels = {}
with gzip.open(os.path.join(directory, "live_parcels.csv.gz"), "rt", newline="") as f:
    # Get address, parcel from each row and put them in Dict as key, value
    for row in csv.DictReader(f):
        if row["ADDRESS"]:
            parcels[row["ADDRESS"]] = row["geometry"]

# Create dictionary of cardinal directions that may appear in addresses with their abbreviations
cardinal_directions = {
    "NORTH": "N",
    "NORTHEAST": "NE",
    "EAST": "E",
    "SOUTHEAST": "SE",
    "SOUTH": "S",
    "SOUTHWEST": "SW",
    "WEST": "W",
    "NORTHWEST": "NW",
}
# Create dictionary that contains all USPS street suffixes and their abbreviations
# Does not include suffixes that are not abbreviated (i.e., "ROW")
# Link to information: https://pe.usps.com/text/pub28/28apc_002.htm
street_suffixes = {
    "ALLEY": "ALY",
    "ANNEX": "ANX",
    "ARCADE": "ARC",
    "AVENUE": "AVE",
    "BAYOU": "BYU",
    "BEACH": "BCH",
    "BEND": "BND",
    "BLUFF": "BLF",
    "BLUFFS": "BLFS",
    "BOTTOM": "BTM",
    "BOULEVARD": "BLVD",
    "BRANCH": "BR",
    "BRIDGE": "BRG",
    "BROOK": "BRK",
    "BROOKS": "BRKS",
    "BURG": "BG",
    "BURGS": "BGS",
    "BYPASS": "BYP",
    "CAMP": "CP",
    "CANYON": "CYN",
    "CAPE": "CPE",
    "CAUSEWAY": "CSWY",
    "CENTER": "CTR",
    "CENTERS": "CTRS",
    "CIRCLE": "CIR",
    "CIRCLES": "CIRS",
    "CLIFF": "CLF",
    "CLIFFS": "CLFS",
    "CLUB": "CLB",
    "COMMON": "CMN",
    "COMMONS": "CMNS",
    "CORNER": "COR",
    "CORNERS": "CORS",
    "COURSE": "CRSE",
    "COURT": "CT",
    "COURTS": "CTS",
    "COVE": "CV",
    "COVES": "CVS",
    "CREEK": "CRK",
    "CRESCENT": "CRES",
    "CREST": "CRST",
    "CROSSING": "XING",
    "CROSSROAD": "XRD",
    "CROSSROADS": "XRDS",
    "CURVE": "CURV",
    "DALE": "DL",
    "DAM": "DM",
    "DIVIDE": "DV",
    "DRIVE": "DR",
    "DRIVES": "DRS",
    "ESTATE": "EST",
    "ESTATES": "ESTS",
    "EXPRESSWAY": "EXPY",
    "EXTENSION": "EXT",
    "EXTENSIONS": "EXTS",
    "FALLS": "FLS",
    "FERRY": "FRY",
    "FIELD": "FLD",
    "FIELDS": "FLDS",
    "FLAT": "FLT",
    "FLATS": "FLTS",
    "FORD": "FRD",
    "FORDS": "FRDS",
    "FOREST": "FRST",
    "FORGE": "FRG",
    "FORGES": "FRGS",
    "FORK": "FRK",
    "FORKS": "FRKS",
    "FORT": "FT",
    "FREEWAY": "FWY",
    "GARDEN": "GDN",
    "GARDENS": "GDNS",
    "GATEWAY": "GTWY",
    "GLEN": "GLN",
    "GLENS": "GLNS",
    "GREEN": "GRN",
    "GREENS": "GRNS",
    "GROVE": "GRV",
    "GROVES": "GRVS",
    "HARBOR": "HBR",
    "HARBORS": "HBRS",
    "HAVEN": "HVN",
    "HEIGHTS": "HTS",
    "HIGHWAY": "HWY",
    "HILL": "HL",
    "HILLS": "HLS",
    "HOLLOW": "HOLW",
    "INLET": "INLT",
    "ISLAND": "IS",
    "ISLANDS": "ISS",
    "JUNCTION": "JCT",
    "JUNCTIONS": "JCTS",
    "KEY": "KY",
    "KEYS": "KYS",
    "KNOLL": "KNL",
    "LAKE": "LK",
    "LAKES": "LKS",
    "LANDING": "LNDG",
    "LANE": "LN",
    "LIGHT": "LGT",
    "LIGHTS": "LGTS",
    "LOAF": "LF",
    "LOCK": "LCK",
    "LOCKS": "LCKS",
    "LODGE": "LDG",
    "MANOR": "MNR",
    "MANORS": "MNRS",
    "MEADOW": "MDW",
    "MEADOWS": "MDWS",
    "MILL": "ML",
    "MILLS": "MLS",
    "MISSION": "MSN",
    "MOTORWAY": "MTWY",
    "MOUNT": "MT",
    "MOUNTAIN": "MTN",
    "MOUNTAINS": "MTNS",
    "NECK": "NCK",
    "ORCHARD": "ORCH",
    "OVERPASS": "OPAS",
    "PARKS": "PARK",
    "PARKWAY": "PKWY",
    "PARKWAYS": "PKWY",
    "PASSAGE": "PSGE",
    "PINE": "PNE",
    "PINES": "PNES",
    "PL": "PLACE",
    "PLAIN": "PLN",
    "PLAINS": "PLNS",
    "PLAZA": "PLZ",
    "POINT": "PT",
    "POINTS": "PTS",
    "PORT": "PRT",
    "PORTS": "PRTS",
    "PRAIRIE": "PR",
    "RADIAL": "RADL",
    "RANCH": "RNCH",
    "RAPID": "RPD",
    "RAPIDS": "RPDS",
    "REST": "RST",
    "RIDGE": "RDG",
    "RIDGES": "RDGS",
    "RIVER": "RIV",
    "ROAD": "RD",
    "ROADS": "RDS",
    "ROUTE": "RTE",
    "SHOAL": "SHL",
    "SHOALS": "SHLS",
    "SHORE": "SHR",
    "SHORES": "SHRS",
    "SKYWAY": "SKWY",
    "SPRING": "SPG",
    "SPRINGS": "SPGS",
    "SPURS": "SPUR",
    "SQUARE": "SQ",
    "SQUARES": "SQS",
    "STATION": "STA",
    "STRAVENUE": "STRA",
    "STREAM": "STRM",
    "STREET": "ST",
    "STREETS": "STS",
    "SUMMIT": "SMT",
    "TERRACE": "TER",
    "THROUGHWAY": "TRWY",
    "TRACE": "TRCE",
    "TRACK": "TRAK",
    "TRAFFICWAY": "TRFY",
    "TRAIL": "TRL",
    "TRAILER": "TRLR",
    "TUNNEL": "TUNL",
    "TURNPIKE": "TPKE",
    "UNDERPASS": "UPAS",
    "UNION": "UN",
    "UNIONS": "UNS",
    "VALLEY": "VLY",
    "VALLEYS": "VLYS",
    "VIADUCT": "VIA",
    "VIEW": "VW",
    "VIEWS": "VWS",
    "VILLAGE": "VLG",
    "VILLAGES": "VLGS",
    "VILLE": "VL",
    "VISTA": "VIS",
    "WALKS": "WALK",
    "WELL": "WL",
    "WELLS": "WLS",
}


# Description
# - Returns the geometry of the parcel associated with a given address.
# Accepts
# - address: str
# Returns
# - parcel: str
def get_parcel(address):
    # Convert input to uppercase
    check_addr = address.upper()
    # Make a list of acceptable address strings - ["EAST 11TH STREET", "E 11TH STREET"], for example
    acceptable = [check_addr]
    # Check the input string for each of the cardinal directions
    dir_normalized = None
    for dir, abbrev in cardinal_directions.items():
        if dir in check_addr:
            # Replace the first instance of the direction with its abbreviation
            dir_normalized = check_addr.replace(dir, abbrev, 1)
        # If this dir isn't in check_addr and dir_normalized hasn't been set:
        elif dir_normalized is None:
            # Set it to check_addr for later - will be replaced if some direction is found, else left alone
            dir_normalized = check_addr
    # Check if the working "normalized" string's street suffix is spelled out (Ex: "DRIVE")
    # Set normalized to dir_normalized for now - if suffix can be abbreviated, this will be replaced
    normalized = dir_normalized
    split_by_word = normalized.split()
    for suffix, shorthand in street_suffixes.items():
        if split_by_word[-1] == suffix:
            # Replace the full suffix with the shorthand version (Ex: "DRIVE" -> "DR")
            normalized = dir_normalized.replace(suffix, shorthand, 1)
    # Append the normalized address string to the "acceptable" list
    acceptable.append(normalized)
    # For debugging: print("ACCEPTABLE LIST: ", acceptable)
    # Grab the parcel associated with address from "parcels" Dict
    for addr in acceptable:
        if addr in parcels:
            return parcels[addr]


# Description
# - Returns the centroid of the parcel located at the input address
# Accepts
# - address: str; the street address
# Returns
# - centroid: shapely.Point; Point with x (longitude) and y (latitude) coordinates that represents centroid
def get_parcel_centroid(address):
    # First, get the parcel's polygon in WKT (string) format
    parcel = get_parcel(address)
    # Then, create a Shapely polygon with the output
    polygon = from_wkt(parcel)
    # Take Shapely's centroid attribute from the polygon and return it
    return polygon.centroid


# "value" is reference to STRTree, "geoms" matches boundary with name of neighborhood
neighborhood_strtree = {"value": None, "geoms": {}}


# Description
# - Returns the neighborhood associations that the input coordinates' point is in, if applicable.
# Accepts
# - longitude: the longitude (y-) coordinate of the input point (can be raw number or string)
# - latitude: the latitude (x-) coordinate of the input point (can be raw number or string)
# - parcel: the WKT polygon of the input parcel (optional and will override latitude/longitude)
# Returns
# - neighborhoods (list of str): the names of the neighborhood associations - empty if N/A
def get_neighborhood_associations(longitude=None, latitude=None, parcel=None):
    # Turn the parcel into a polygon that we can get map with neighborhoods
    if parcel is not None:
        query_geom = from_wkt(parcel)
    # Else, we just need to make a point out of the input longitude and latitude
    else:
        query_geom = Point(longitude, latitude)

    # Load address index for tree upon first run of the function
    if neighborhood_strtree["value"] is None:
        with gzip.open(
            os.path.join(directory, "neighborhoods.csv.gz"),
            "rt",
            newline="",
            encoding="utf-8",
        ) as f:
            # Fill "geoms" dictionary with data from CSV in the format of "boundary": name
            for row in csv.DictReader(f):
                geom = from_wkt(row["boundary"])
                if row["name"]:
                    neighborhood_strtree["geoms"][geom] = row["name"]
            # Create the STRtree and store the reference to it in "value" for later use
            neighborhood_strtree["value"] = STRtree(
                [geom for geom, name in neighborhood_strtree["geoms"].items()]
            )

    # Grab index of all geometries (neighborhood associations) that the point intersects
    neighborhood_indices = neighborhood_strtree["value"].query(
        query_geom, predicate="intersects"
    )
    # Grab actual geometries of neighborhoods intersecting point and store them in list
    neighborhood_geometries = [
        neighborhood_strtree["value"].geometries[index]
        for index in neighborhood_indices
    ]
    # Create the list of neighborhoods associated with the point by indexing "geoms" with neighborhood geoms
    neighborhoods = [neighborhood_strtree["geoms"][g] for g in neighborhood_geometries]
    # Return result
    return neighborhoods


# Open the intersections.csv.gz file and grab the first (and only) row containing the intersection data
with gzip.open(
    os.path.join(directory, "intersections.csv.gz"), "rt", newline="", encoding="utf-8"
) as f:
    r = csv.DictReader(f)
    intersections = next(r)


# Description
# - Returns the longitude and latitude coordinates for a specified intersection (ex: "11th St & Market St")
# Accepts
# - name (string): the name of the streets/roads that intersect, in the format of "[Street1] & [Street2]"
# Returns
# - coordinates (list of numbers): the longitude (x-) and latitude (y-) coordinates of the intersection
# Note
# - return value will be None if the specified intersection can not be found
def get_intersection_coordinates(name):
    # Allow the user to input "at" instead of "&" by standardizing their input to "&"
    if name.count(" at ") != 0:
        name = name.replace(" at ", " & ")
    elif name.count(" and ") != 0:
        name = name.replace(" and ", " & ")

    # If the user input a direction for either of the street names, remove it
    streets = name.split(" & ")
    fixed = []
    for street in streets:
        contains_direction = r"\b[NESW]+\b\s|\s\b[NESW]+\b"
        if bool(re.search(contains_direction, street)):
            street = re.sub(contains_direction, "", street)
        fixed.append(street)

    # Make sure the streets are in alphabetical order
    fixed.sort()

    # Put the street names back together
    name = " & ".join(fixed)

    coordinates = []
    # Access intersection coords using name as key into intersections dictionary
    if name in intersections:
        intersection = from_wkt(intersections[name])
        coordinates.append(intersection.x)
        coordinates.append(intersection.y)
        # Return list with coordinates
        return coordinates


def main():
    parser = argparse.ArgumentParser(
        prog="geochatt",
        description="Utility Functions for Working with Open GeoSpatial Data about Chattanooga",
    )
    parser.add_argument(
        "method",
        help='method to run, can be "get-address", "get-city-council-district", "get-parcel", "get-parcel-centroid", "get-zipcode"',
    )
    parser.add_argument("--address", type=str, help="address")
    parser.add_argument("--latitude", type=float, help="latitude")
    parser.add_argument("--longitude", type=float, help="latitude")
    args = parser.parse_args()
    # print("args:", args)

    if args.method in ["get-address", "get_address"]:
        print(get_address(latitude=args.latitude, longitude=args.longitude))
    elif args.method in ["get-city-council-district", "get_city_council_district"]:
        print(
            get_city_council_district(latitude=args.latitude, longitude=args.longitude)
        )
    elif args.method in ["get-municipality", "get_municipality"]:
        print(get_municipality(latitude=args.latitude, longitude=args.longitude))
    elif args.method in ["get-zipcode", "get_zipcode"]:
        print(get_zipcode(latitude=args.latitude, longitude=args.longitude))
    elif args.method in ["get-parcel", "get_parcel"]:
        print(get_parcel(address=args.address))
    elif args.method in ["get-parcel-centroid", "get_parcel_centroid"]:
        print(get_parcel_centroid(address=args.address))


if __name__ == "__main__":
    main()
