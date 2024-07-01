""" Update installed capacity in database

We now do this in the app, so we dont need to run this anymore
"""

import json
import os

import boto3
import pandas as pd
import requests
from nowcasting_datamodel.connection import DatabaseConnection
from nowcasting_datamodel.models.base import Base_Forecast
from nowcasting_datamodel.read.read import get_all_locations

import gspconsumer

# get db connection from database
client = boto3.client("secretsmanager")
response = client.get_secret_value(
    SecretId="development/rds/forecast/",
)
secret = json.loads(response["SecretString"])
""" We have used a ssh tunnel to 'localhost' """
db_url = f'postgresql://{secret["username"]}:{secret["password"]}@localhost:5433/{secret["dbname"]}'
connection = DatabaseConnection(url=db_url, base=Base_Forecast, echo=True)

# get installed cpapacity from file
file = "data/pv_capacity_by_20220314_GSP.csv"
dir = os.path.dirname(gspconsumer.__file__) + "/../scripts/v3_to_v4/"
installed_capacity = pd.read_csv(f"{dir}/{file}")

# gsps names
url = "https://api0.solar.sheffield.ac.uk/pvlive/api/v4/gsp_list"
respsone = requests.get(url=url)
d = json.loads(respsone.text)
gsps = pd.DataFrame(data=d["data"], columns=d["meta"])
gsps["GSPs"] = gsps["gsp_name"]


# get installed cpapacity from file
file = "data/pv_capacity_by_20220314_GSP.csv"
dir = os.path.dirname(gspconsumer.__file__) + "/../scripts/v3_to_v4/"
installed_capacity = pd.read_csv(f"{dir}/{file}")

# add national
total_installed_capacity_mw = installed_capacity["dc_capacity_MWp"].sum()
national = pd.DataFrame(
    columns=["GSPs", "dc_capacity_MWp"], data=[["NATIONAL", total_installed_capacity_mw]]
)
installed_capacity = pd.concat([national, installed_capacity])
installed_capacity.reset_index(inplace=True, drop=True)

# remove unknown
installed_capacity = installed_capacity[installed_capacity["GSPs"] != "unknown"]

# merge with GSPs names
installed_capacity = gsps.merge(installed_capacity, on="GSPs", how="left")
installed_capacity = installed_capacity.fillna(0)
installed_capacity.loc[0, "GSPs"] = "National"

# update each gsp location
with connection.get_session() as session:
    locations = get_all_locations(session=session)

    for location in locations:
        gsp_id = location.gsp_id
        print(gsp_id)

        if gsp_id >= len(installed_capacity):
            break

        gsp_details = installed_capacity[installed_capacity["gsp_id"] == gsp_id].iloc[0]

        location.installed_capacity_mw = gsp_details.dc_capacity_MWp
        location.region_name = gsp_details.GSPs
        location.gsp_name = gsp_details.GSPs
        location.gsp_group = gsp_details.GSPs

    # update database
    print("Updating database")
    session.commit()
