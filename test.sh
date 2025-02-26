#!/bin/bash -e

test_get_address () {
    result=$(geochatt get-address --latitude="35.0432979" --longitude="-85.3076591")
    if [[ "$result" = "101 E 11TH ST" ]]; then
        echo "PASSED test_get_address"
    else
        echo 'FAILED test_get_address'
        exit 1
    fi
}

test_get_city_council_district () {
    result=$(geochatt get-city-council-district --latitude="35.0432979" --longitude="-85.3076591")
    if [[ "$result" = "8" ]]; then
        echo "PASSED test_get_city_council_district"
    else
        echo 'FAILED test_get_city_council_district'
        exit 1
    fi
}

test_get_municipality () {
    result=$(geochatt get-municipality --latitude="35.0432979" --longitude="-85.3076591")
    if [[ "$result" = "Chattanooga" ]]; then
        echo "PASSED test_get_municipality"
    else
        echo 'FAILED test_get_municipality'
        exit 1
    fi
}

test_get_parcel () {
    result=$(geochatt get-parcel --address="101 east 11th street")
    if [[ "$result" = "POLYGON ((-85.3069572 35.043897, -85.3074818 35.0440926, -85.3075952 35.0438743, -85.3078311 35.0434433, -85.3073192 35.0432494, -85.3069718 35.0438707, -85.3069572 35.043897))" ]]; then
        echo "PASSED test_get_parcel"
    else
        echo 'FAILED test_get_parcel'
        exit 1
    fi
}

test_get_parcel_centroid () {
    result=$(geochatt get-parcel-centroid --address="101 east 11th street")
    if [[ "$result" = "POINT (-85.30739570641228 35.0436712625469)" ]]; then
        echo "PASSED test_get_parcel_centroid"
    else
        echo 'FAILED test_get_parcel_centroid'
        exit 1
    fi
}

test_get_zipcode () {
    result=$(geochatt get-zipcode --latitude="35.0432979" --longitude="-85.3076591")
    if [[ "$result" = "37402" ]]; then
        echo "PASSED test_get_zipcode"
    else
        echo 'FAILED test_get_zipcode'
        exit 1
    fi
}


test_get_address
test_get_city_council_district
test_get_municipality
test_get_parcel
test_get_parcel_centroid
test_get_zipcode
