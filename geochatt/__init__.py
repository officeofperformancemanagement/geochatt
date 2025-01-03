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


# Create dictionary of cardinal directions that may appear in addresses with their abbreviations
cardinal_directions = {
    "NORTH": "N", "NORTHEAST": "NE", "EAST": "E", "SOUTHEAST": "SE", 
    "SOUTH": "S", "SOUTHWEST": "SW", "WEST": "W", "NORTHWEST": "NW"
}
# Create dictionary that contains all USPS street suffixes and their abbreviations
# Does not include suffixes that are not abbreviated (i.e., "ROW")
# Link to information: https://pe.usps.com/text/pub28/28apc_002.htm
street_suffixes = {
    "ALLEY": "ALY", "ANNEX": "ANX", "ARCADE": "ARC", "AVENUE": "AVE", "BAYOU": "BYU", "BEACH": "BCH", 
    "BEND": "BND", "BLUFF": "BLF", "BLUFFS": "BLFS", "BOTTOM": "BTM", "BOULEVARD": "BLVD", "BRANCH": "BR", 
    "BRIDGE": "BRG", "BROOK": "BRK", "BROOKS": "BRKS", "BURG": "BG", "BURGS": "BGS", "BYPASS": "BYP", 
    "CAMP": "CP", "CANYON": "CYN", "CAPE": "CPE", "CAUSEWAY": "CSWY", "CENTER": "CTR", "CENTERS": "CTRS", 
    "CIRCLE": "CIR", "CIRCLES": "CIRS", "CLIFF": "CLF", "CLIFFS": "CLFS", "CLUB": "CLB", "COMMON": "CMN", 
    "COMMONS": "CMNS", "CORNER": "COR", "CORNERS": "CORS", "COURSE": "CRSE", "COURT": "CT", "COURTS": "CTS", 
    "COVE": "CV", "COVES": "CVS", "CREEK": "CRK", "CRESCENT": "CRES", "CREST": "CRST", "CROSSING": "XING", 
    "CROSSROAD": "XRD", "CROSSROADS": "XRDS", "CURVE": "CURV", "DALE": "DL", "DAM": "DM", "DIVIDE": "DV", 
    "DRIVE": "DR", "DRIVES": "DRS", "ESTATE": "EST", "ESTATES": "ESTS", "EXPRESSWAY": "EXPY", 
    "EXTENSION": "EXT", "EXTENSIONS": "EXTS", "FALLS": "FLS", "FERRY": "FRY", "FIELD": "FLD", 
    "FIELDS": "FLDS", "FLAT": "FLT", "FLATS": "FLTS", "FORD": "FRD", "FORDS": "FRDS", "FOREST": "FRST", 
    "FORGE": "FRG", "FORGES": "FRGS", "FORK": "FRK", "FORKS": "FRKS", "FORT": "FT", "FREEWAY": "FWY", 
    "GARDEN": "GDN", "GARDENS": "GDNS", "GATEWAY": "GTWY", "GLEN": "GLN", "GLENS": "GLNS", "GREEN": "GRN", 
    "GREENS": "GRNS", "GROVE": "GRV", "GROVES": "GRVS", "HARBOR": "HBR", "HARBORS": "HBRS", "HAVEN": "HVN", 
    "HEIGHTS": "HTS", "HIGHWAY": "HWY", "HILL": "HL", "HILLS": "HLS", "HOLLOW": "HOLW", "INLET": "INLT", 
    "ISLAND": "IS", "ISLANDS": "ISS", "JUNCTION": "JCT", "JUNCTIONS": "JCTS", "KEY": "KY", 
    "KEYS": "KYS", "KNOLL": "KNL", "LAKE": "LK", "LAKES": "LKS", "LANDING": "LNDG", 
    "LANE": "LN", "LIGHT": "LGT", "LIGHTS": "LGTS", "LOAF": "LF", "LOCK": "LCK", "LOCKS": "LCKS", 
    "LODGE": "LDG", "MANOR": "MNR", "MANORS": "MNRS", "MEADOW": "MDW", 
    "MEADOWS": "MDWS", "MILL": "ML", "MILLS": "MLS", "MISSION": "MSN", "MOTORWAY": "MTWY", 
    "MOUNT": "MT", "MOUNTAIN": "MTN", "MOUNTAINS": "MTNS", "NECK": "NCK", "ORCHARD": "ORCH", 
    "OVERPASS": "OPAS", "PARKS": "PARK", "PARKWAY": "PKWY", "PARKWAYS": "PKWY", 
    "PASSAGE": "PSGE", "PINE": "PNE", "PINES": "PNES", 
    "PL": "PLACE", "PLAIN": "PLN", "PLAINS": "PLNS", "PLAZA": "PLZ", "POINT": "PT", "POINTS": "PTS", 
    "PORT": "PRT", "PORTS": "PRTS", "PRAIRIE": "PR", "RADIAL": "RADL", "RANCH": "RNCH", 
    "RAPID": "RPD", "RAPIDS": "RPDS", "REST": "RST", "RIDGE": "RDG", "RIDGES": "RDGS", "RIVER": "RIV", 
    "ROAD": "RD", "ROADS": "RDS", "ROUTE": "RTE", "SHOAL": "SHL", 
    "SHOALS": "SHLS", "SHORE": "SHR", "SHORES": "SHRS", "SKYWAY": "SKWY", "SPRING": "SPG", 
    "SPRINGS": "SPGS", "SPURS": "SPUR", "SQUARE": "SQ", "SQUARES": "SQS", "STATION": "STA", 
    "STRAVENUE": "STRA", "STREAM": "STRM", "STREET": "ST", "STREETS": "STS", "SUMMIT": "SMT", 
    "TERRACE": "TER", "THROUGHWAY": "TRWY", "TRACE": "TRCE", "TRACK": "TRAK", "TRAFFICWAY": "TRFY", 
    "TRAIL": "TRL", "TRAILER": "TRLR", "TUNNEL": "TUNL", "TURNPIKE": "TPKE", "UNDERPASS": "UPAS", 
    "UNION": "UN", "UNIONS": "UNS", "VALLEY": "VLY", "VALLEYS": "VLYS", "VIADUCT": "VIA", "VIEW": "VW", 
    "VIEWS": "VWS", "VILLAGE": "VLG", "VILLAGES": "VLGS", "VILLE": "VL", "VISTA": "VIS", 
    "WALKS": "WALK", "WELL": "WL", "WELLS": "WLS"
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
    # Open the parcel data file
    with gzip.open(
        os.path.join(directory, "live_parcels.csv.gz"), "rt", newline=""
    ) as f:
        # Read each row and compare its address to the target
        for row in csv.DictReader(f):
            if row["ADDRESS"]:
                if row["ADDRESS"] in acceptable:
                    # Return the target address's parcel geometry
                    return row["geometry"]


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
