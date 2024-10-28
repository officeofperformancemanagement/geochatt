#!/bin/bash -e

# download zipcodes
curl --output "./geochatt/zipcodes.geojson" "https://www.chattadata.org/resource/kwzr-kyn5.geojson"

# download municipalities
curl --output "./geochatt/municipalities.geojson" "https://mapsdev.hamiltontn.gov/hcwa03/rest/services/OpenGov/OpenGov_HamiltonTN/MapServer/19/query?where=1%3D1&text=&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&relationParam=&outFields=*&returnGeometry=true&returnTrueCurves=false&maxAllowableOffset=&geometryPrecision=&outSR=&having=&returnIdsOnly=false&returnCountOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&gdbVersion=&historicMoment=&returnDistinctValues=false&resultOffset=&resultRecordCount=&queryByDistance=&returnExtentOnly=false&datumTransformation=&parameterValues=&rangeValues=&quantizationParameters=&f=geojson"

# download city council districts
curl --output "./geochatt/city_council_districts.geojson" "https://www.chattadata.org/resource/5t2x-jnde.geojson"

# download parcels
python prepare_parcels.py
