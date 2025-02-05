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

    #print(response_data["features"])#

    # If this is less than 2,000 after the following "for" loop, then this is the last page of results
    count_features = 0

    # Isolate the geojson feature names and geometries
    for feature in response_data["features"]:
        name = feature["properties"]["Name"]
        if feature["properties"]["TypeSuffix"] is not None:
            name += " " + feature["properties"]["TypeSuffix"]
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
        touching_indices = linestring_strtree["value"].query(endpoint, predicate="touches")
        # There may not be any touching geometries - only run the following code if there are any
        if len(touching_indices) >= 1:
            # Get the actual touching geometries
            touching_geometries = [linestring_strtree["value"].geometries[index] for index in touching_indices]
            # Get the coordinate of the intersection with the first touching geometry
            intersection_coordinate = endpoint.intersection(touching_geometries[0])
            # Gather all the street names associated with the intersection
            street_names_list = []
            for t in touching_geometries:
                street_names_list.append(linestring_strtree["geoms"][t])
            # Get all combinations of two street names from the street_names_list as a list
            street_combinations = list(itertools.combinations(street_names_list, 2))
            # For each combination, make a key out of it and set its value to the coordinate
            for combination in street_combinations:
                # Format as "[Street1] & [Street2]"
                intersection_name = combination[0] + " & " + combination[1]
                # Add to dictionary inside of intersection_data list
                intersection_data[0][intersection_name] = intersection_coordinate

"""
Now, the data just needs to be written to a csv.gz file. Because all of the data is kept in a single
dictionary inside of intersection_data, there is only one row to write. The keys of this dictionary serve as
the fieldnames.
"""

with gzip.open("./geochatt/intersections.csv.gz", "wt", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=intersection_data[0].keys())
    writer.writeheader()
    writer.writerows(intersection_data)