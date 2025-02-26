# geochatt
Utility Functions for Working with Open GeoSpatial Data about Chattanooga

## features
- very fast: uses [STRTree](https://shapely.readthedocs.io/en/2.0.4/strtree.html) for super fast reverse geocoding
- get address from point
- get city council district from point
- get municipality from point
- get zip code from point

## install
```sh
pip install geochatt
```

## usage
```py
import geochatt

geochatt.get_address(longitude=-85.3076591, latitude=35.0432979)
"101 E 11TH ST"

geochatt.get_city_council_district(longitude=-85.3076591, latitude=35.0432979)
8

geochatt.get_municipality(longitude=-85.3076591, latitude=35.0432979)
"Chattanooga"

geochatt.get_zipcode(longitude=-85.3076591, latitude=35.0432979)
37402

# get_parcel returns a string representing a Well-known text-format polygon
geochatt.get_parcel(address="101 E 11TH ST")
'POLYGON ((-85.3069572 35.043897, -85.3074818 35.0440926, -85.3075952 35.0438743, -85.3078311 35.0434433, -85.3073192 35.0432494, -85.3069718 35.0438707, -85.3069572 35.043897))'

# get_parcel_centroid returns a Shapely Point object
geochatt.get_parcel_centroid(address="101 E 11TH ST")
<POINT (-85.307 35.044)>
```

## cli usage
```sh
$ pip install geochatt

$ geochatt get-address --latitude="35.0432979" --longitude="-85.3076591"
101 E 11TH ST

$ geochatt get-city-council-district --latitude="35.0432979" --longitude="-85.3076591"
8

$ geochatt get-municipality --latitude="35.0432979" --longitude="-85.3076591"
Chattanooga

$ geochatt get-parcel --address="101 east 11th street"
POLYGON ((-85.3069572 35.043897, -85.3074818 35.0440926, -85.3075952 35.0438743, -85.3078311 35.0434433, -85.3073192 35.0432494, -85.3069718 35.0438707, -85.3069572 35.043897))

$ geochatt get-parcel-centroid --address="101 east 11th street"
POINT (-85.30739570641228 35.0436712625469)

$ geochatt get-zipcode --latitude="35.0432979" --longitude="-85.3076591"
37402
```

## performance
Reverse geocoding is super fast thanks to [STRTree](https://shapely.readthedocs.io/en/2.0.4/strtree.html).
The performance test of geocoding 1 million random points takes 122.900 seconds, which is 0.000122 seconds per point.
