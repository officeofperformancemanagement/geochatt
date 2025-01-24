import random
import unittest

import geochatt

class TestCityHall(unittest.TestCase):
    # City Hall coordinates: 35.04379983455412, -85.30815077048146
    def test_get_neighborhood_associations(self):
        result = geochatt.get_neighborhood_associations(longitude="-85.30815077048146", latitude="35.04379983455412")
        self.assertEqual(result, ["Martin Luther King Neighborhood Association"])
    
    def test_get_parcel_centroid(self):
            result = geochatt.get_parcel_centroid(address="101 EAST 11TH ST")
            # Please Note: The centroid is printed so that its coordinates can be validated on geojson.io.
            # Here is a link to the website: https://geojson.io/#map=2/0/20
            # Go to Chattanooga Municipal Building (address above), click the teardrop-shaped icon on the right,
            # and click in the middle of the property. The coordinates should be similar--not like a degree off.
            # print("RESULT OF TEST_GET_PARCEL_CENTROID (101 EAST 11TH ST): ", result)
            # Test each point to see if results match previous tests
            # These were the results collected in December of 2024, so changes to shapely could cause them to be unequal
            self.assertEqual(result.x, -85.30739570641228)
            self.assertEqual(result.y, 35.0436712625469)

    def test_get_parcel(self):
        result = geochatt.get_parcel(address="101 east 11th street")
        self.assertEqual(
            result,
            "POLYGON ((-85.3069572 35.043897, -85.3074818 35.0440926, -85.3075952 35.0438743, -85.3078311 35.0434433, -85.3073192 35.0432494, -85.3069718 35.0438707, -85.3069572 35.043897))",
        )

    def test_get_address(self):
        result = geochatt.get_address(latitude=35.0432979, longitude=-85.3076591)
        self.assertEqual(result, "101 E 11TH ST")

    def test_get_city_council_district(self):
        result = geochatt.get_city_council_district(
            latitude=35.0432979, longitude=-85.3076591
        )
        self.assertEqual(result, 8)

    def test_get_municipality(self):
        result = geochatt.get_municipality(latitude=35.0432979, longitude=-85.3076591)
        self.assertEqual(result, "Chattanooga")

    def test_get_zipcode(self):
        result = geochatt.get_zipcode(longitude=-85.3076591, latitude=35.0432979)
        self.assertEqual(result, 37402)


class TestPerformance(unittest.TestCase):
    def test_1_million_random_points(self):
        xmin = -85.12039589514865
        xmax = -85.35984115038111
        xrange = xmax - xmin
        ymin = 34.9885572083127
        ymax = 35.08995423286255
        yrange = ymax - ymin

        for i in range(1_000_000):
            x = xmin + random.random() * xrange
            y = ymin + random.random() * yrange
            geochatt.get_address(longitude=x, latitude=y)
            geochatt.get_parcel("101 E 11TH ST")
            geochatt.get_neighborhood_associations(longitude="-85.30815077048146", latitude="35.04379983455412")
            


if __name__ == "__main__":
    unittest.main()
