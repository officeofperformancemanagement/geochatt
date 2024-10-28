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
```

## performance
Reverse geocoding is super fast thanks to [STRTree](https://shapely.readthedocs.io/en/2.0.4/strtree.html).
The performance test of geocoding 1 million random points takes 122.900 seconds, which is 0.000122 seconds per point.
