""" to make gsp to dno mappings """

import json
import os

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import requests

# load gsp files
url = (
    "https://data.nationalgrideso.com/backend/dataset/2810092e-d4b2-472f-b955-d8bea01f9ec0/"
    "resource/08534dae-5408-4e31-8639-b579c8f1c50b/download/gsp_regions_20220314.geojson"
)

response = requests.get(url)
shape_gpd = gpd.read_file(response.text)

# load gsp files from database
url = os.getenv("DB_URL")
gsp = pd.read_sql("select * from location order by gsp_id", url)

shape_gpd["gsp_name"] = shape_gpd["GSPs"]
shape_gpd = shape_gpd.merge(gsp, on="gsp_name", how="left")

# GSPGROUP name, I think is DNO

# load dno files just incase
# url = "https://data.nationalgrideso.com/backend/dataset/0e377f16-95e9-4c15-a1fc-49e06a39cfa0/resource/e96db306-aaa8-45be-aecd-65b34d38923a/download/dno_license_areas_20200506.geojson"  # noqa
# dno_shapes = gpd.read_file(url)

# sort by gsp mapping
shape_gpd.sort_values("GSPGroup", inplace=True)


# group by GSPGroup
def join_two_rows_together(x, y, gdf):
    if x.GSPGroup == y.GSPGroup:
        gdf = gdf.copy()
        geom = x.geometry.union(y.geometry)
        geom = gpd.GeoSeries(geom, index=[x.name])
        gdf.loc[gdf.index == x.name, "geometry"] = geom.geometry
        gdf.loc[gdf.index == x.name, "gsp_ids"] += "," + str(y.gsp_id)
        gdf.loc[gdf.index == x.name, "installed_capacity_mw"] += y.installed_capacity_mw

        # drop row
        print(f"dropping {y.name}")
        gdf = gdf.drop(y.name)

        drop = True

    else:
        print(f"skipping {x.GSPGroup} and {y.GSPGroup} as they are different")
        drop = False

    return gdf.copy(), drop


# shape_gpd_all = shape_gpd
# shape_gpd = shape_gpd_all
shape_gpd.reset_index(inplace=True)
j = 0
shape_gpd["gsp_ids"] = shape_gpd["gsp_id"].astype(str)
for i in range(1, len(shape_gpd)):
    print(j, i)

    x = shape_gpd.iloc[j]
    y = shape_gpd.iloc[j + 1]

    shape_gpd, drop = join_two_rows_together(x, y, shape_gpd)
    if not drop:
        j = j + 1

# save to csv
gsp = shape_gpd[["GSPGroup", "gsp_ids", "installed_capacity_mw"]]
gsp.to_csv("gsp_dno_mapping.csv", index=False)

# lets plot it
shape_gpd.reset_index(inplace=True, drop=True)
shape_gpd = shape_gpd.to_crs(epsg=4326)
shapes_dict = json.loads(shape_gpd.to_json())

fig = go.Figure()
fig.add_trace(
    go.Choroplethmapbox(
        geojson=shapes_dict,
        locations=shape_gpd.index.values,
        z=shape_gpd["installed_capacity_mw"].values,
        colorscale="Viridis",
    )
)

fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=4, mapbox_center={"lat": 55, "lon": 0})
fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 30})
fig.show(renderer="browser")

# save html
fig.write_html("gsp_dno_mapping.html")
