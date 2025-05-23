import csv
import gzip
import itertools
import json
import requests
import shapely

"""
This program queries the HC_Base Block_lc data, collecting each road in Hamilton County as a geospatial 
object, then using this data to construct a data set of intersections, with each row having the names of the 
intersecting streets and the latitude and longitude coordinates of the intersection.

Source: https://pwgis.chattanooga.gov/server/rest/services/HC_Base/Block_lc/MapServer/0/query

Each query returns only 2,000 objects at maximum -- therefore, several queries must be run in order to gather
all of the data.
"""

# Used to access results beyond the first 2,000 - increment by 2,000 upon each iteration of the loop
result_offset = 0

# Create dictionary with geometries as keys and their names as values
line_strings = {}

for i in range(1_000_000_000_000):
    # Construct the URL to query the data
    url = "https://pwgis.chattanooga.gov/server/rest/services/HC_Base/Block_lc/MapServer/0/query?where=1%3D1&outFields=*"
    if result_offset != 0:
        url += "&resultOffset=" + str(result_offset)
    url += "&f=geojson"

    # Query the data using requests and grab the content of the response
    content = requests.get(url=url).content

    # Load the response data as JSON (dictionary)
    response_data = json.loads(content)

    # print(response_data["features"])#

    # If this is less than 2,000 after the following "for" loop, then this is the last page of results
    count_features = 0

    # Isolate the geojson feature names and geometries
    for feature in response_data["features"]:
        name = feature["properties"]["Name"]
        if feature["properties"]["TypeSuffix"] is not None:
            name += f"/{feature["properties"]["TypeSuffix"]}"
        # Some features are LineStrings while others are MultiLineString - make the appropriate Shapely object
        if feature["geometry"]["type"] == "LineString":
            geometry = shapely.LineString(feature["geometry"]["coordinates"])
        elif feature["geometry"]["type"] == "MultiLineString":
            geometry = shapely.MultiLineString(feature["geometry"]["coordinates"])
        # Add to dictionary
        line_strings[geometry] = name
        # Increment count_features
        count_features += 1

    # Break the loop once the last page of results is saved
    if count_features < 2_000:
        break

    # Increment result_offset by 2,000
    result_offset += 2_000

# Make a list that will contain a single row (dictionary) with all data to write to CSV
intersection_data = [{}]

"""
Now that all geometries have been loaded, we need to find all of the intersection points. This shall be
accomplished by setting up an STR-Tree containing the geometries, then querying it with the predicate
"touches" for each geometry to find which other ones meet with it. 
"""

linestring_strtree = {"value": None, "geoms": line_strings}

# Load memory index of STR-Tree upon creation
if linestring_strtree["value"] is None:
    linestring_strtree["value"] = shapely.STRtree(
        [geom for geom, name in linestring_strtree["geoms"].items()]
    )

for geom in linestring_strtree["geoms"]:
    # Get the endpoints of the geom
    endpoints = []
    # If it is a LineString, simply get the first and last coordinates
    if geom.geom_type == "LineString":
        endpoints.append(geom.coords[0])
        endpoints.append(geom.coords[-1])
    # If it is a MultiLineString, get the first coord of the first line and the last coord of the last line
    elif geom.geom_type == "MultiLineString":
        endpoints.append(geom.geoms[0].coords[0])
        endpoints.append(geom.geoms[-1].coords[-1])
    for endpt in endpoints:
        endpoint = shapely.Point(endpt)
        # Get the indices of the touching geometries
        touching_indices = linestring_strtree["value"].query(
            endpoint, predicate="touches"
        )
        # There may not be any touching geometries - only run the following code if there are any
        if len(touching_indices) >= 1:
            # Get the actual touching geometries
            touching_geometries = [
                linestring_strtree["value"].geometries[index]
                for index in touching_indices
            ]
            # Get the coordinate of the intersection with the first touching geometry
            intersection_coordinate = endpoint.intersection(touching_geometries[0])
            # Gather all the street names associated with the intersection
            street_names_list = []
            for t in touching_geometries:
                street_names_list.append(linestring_strtree["geoms"][t])
            # # Get all combinations of two street names from the street_names_list as a list
            # street_combinations = list(itertools.combinations(street_names_list, 2))
            # # For each combination, make a key out of it and set its value to the coordinate
            # for combination in street_combinations:
            #     # Format as "[Street1] & [Street2]"
            #     intersection_name = f"{combination[0]} & {combination[1]}"
            #     # Add to dictionary inside of intersection_data list
            #     intersection_data[0][intersection_name] = intersection_coordinate

            """
            We want to append a record to the dictionary for all possible permutations of the names.
            For example, for A Rd and B St, there would be:
                1. A & B
                2. A Rd & B
                3. A & B St
                4. A Rd & B St
                ...as well as the reverse order, so B Rd & A St, and so on.
            The names are currently formated like name/suffix, so these would be A/Rd and B/St.
            """

            # Get all combinations of two street names from the street_names_list as a list
            street_combinations = list(itertools.combinations(street_names_list, 2))
            # For each combination, save a key-value pair for each permutation and the coordinate
            for combination in street_combinations:
                # s1: first street in combination
                s1split = combination[0].split("/")
                s1name = s1split[0]
                if len(s1split) > 1:
                    s1suffix = s1split[1]
                else:
                    s1suffix = None
                # s2: second street in combination
                s2split = combination[1].split("/")
                s2name = s2split[0]
                if len(s2split) > 1:
                    s2suffix = s2split[1]
                else:
                    s2suffix = None
                # Permutations
                perms = [
                    f"{s1name} & {s2name}",
                    f"{s1name} {s1suffix} & {s2name}",
                    f"{s1name} & {s2name} {s2suffix}",
                    f"{s1name} {s1suffix} & {s2name} {s2suffix}",
                    f"{s2name} & {s1name}",
                    f"{s2name} {s2suffix} & {s1name}",
                    f"{s2name} & {s1name} {s1suffix}",
                    f"{s2name} {s2suffix} & {s1name} {s1suffix}",
                ]
                # For each permutation, create the key-value pair in the intersection_data dictionary
                for perm in perms:
                    intersection_data[0][perm] = intersection_coordinate

"""
Now, the data just needs to be written to a csv.gz file. Because all of the data is kept in a single
dictionary inside of intersection_data, there is only one row to write. The keys of this dictionary serve as
the fieldnames.
"""

with gzip.open(
    "./geochatt/intersections.csv.gz", "wt", newline="", encoding="utf-8"
) as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=intersection_data[0].keys())
    writer.writeheader()
    writer.writerows(intersection_data)
