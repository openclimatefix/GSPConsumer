""" Get GSP regions from National Grid API"""

from urllib.request import urlopen

import geopandas as gpd

url_v3 = (
    "https://data.nationalgrideso.com/backend/dataset/2810092e-d4b2-472f-b955-d8bea01f9ec0/"
    "resource/a3ed5711-407a-42a9-a63a-011615eea7e0/download/gsp_regions_20181031.geojson"
)

url_v4 = (
    "https://data.nationalgrideso.com/backend/dataset/2810092e-d4b2-472f-b955-d8bea01f9ec0/"
    "resource/08534dae-5408-4e31-8639-b579c8f1c50b/download/gsp_regions_20220314.geojson"
)


with urlopen(url_v3) as response:
    shape_gpd = gpd.read_file(response)

    shape_gpd.to_file("./gsp_regions_20181031.geojson")


with urlopen(url_v4) as response:
    shape_gpd = gpd.read_file(response)

    shape_gpd.to_file("./gsp_regions_20220314.geojson")
