from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, "README.md")) as f:
    long_description = f.read()

setup(
    name="geochatt",
    packages=["geochatt"],
    package_dir={"geochatt": "geochatt"},
    package_data={
        "geochatt": [
            "__init__.py",
            "city_council_districts.geojson",
            "live_parcels.csv.gz",
            "municipalities.geojson",
            "zipcodes.geojson",
        ]
    },
    version="0.0.1",
    description="Utility Functions for Working with Open GeoSpatial Data about Chattanooga",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Daniel J. Dufour",
    author_email="daniel.j.dufour@gmail.com",
    url="https://github.com/officeofperformancemanagement/geochatt",
    download_url="https://github.com/officeofperformancemanagement/geochatt/tarball/download",
    keywords=["data", "python"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Operating System :: OS Independent",
    ],
    install_requires=["shapely"],
)
