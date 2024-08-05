"""
Update database with gsp details

1. load locations from database
2. load installed capacity mw from pv live
3. load GSP details from ESO
4. update database
"""

import json
from datetime import datetime, timezone

import boto3
from nowcasting_datamodel.connection import DatabaseConnection
from nowcasting_datamodel.models.base import Base_Forecast
from nowcasting_datamodel.read.read import get_all_locations, get_location
from nowcasting_dataset.data_sources.gsp.eso import get_gsp_metadata_from_eso
from pvlive_api import PVLive

client = boto3.client("secretsmanager")
response = client.get_secret_value(
    SecretId="development/rds/forecast/",
)
secret = json.loads(response["SecretString"])
""" We have used a ssh tunnel to 'localhost' """
db_url = f'postgresql://{secret["username"]}:{secret["password"]}@localhost:5433/{secret["dbname"]}'

connection = DatabaseConnection(url=db_url, base=Base_Forecast, echo=True)
pvl = PVLive()
eso = get_gsp_metadata_from_eso()

with connection.get_session() as session:
    locations = get_all_locations(session=session)
    print(locations[0].__dict__)

    national_location = get_location(session=session, gsp_id=0)
    print(national_location.__dict__)
    locations = [national_location] + locations

    for location in locations:
        gsp_id = location.gsp_id
        print(gsp_id)

        # load installed capacity from pv live
        print("Getting information pv live")
        d = pvl.at_time(
            datetime(2022, 5, 1, tzinfo=timezone.utc),
            entity_type="gsp",
            extra_fields="installedcapacity_mwp",
            dataframe=True,
            entity_id=gsp_id,
        )

        # add installed capacity
        installedcapacity_mwp = d.iloc[0].installedcapacity_mwp
        location.installed_capacity_mw = installedcapacity_mwp

        # add labels
        if gsp_id == 0:
            location.region_name = "National"
            location.gsp_name = "National"
            location.gsp_group = "National"
        else:
            details = eso[eso["gsp_id"] == gsp_id]
            location.region_name = details.iloc[0].RegionName
            location.gsp_name = details.iloc[0].gsp_name
            location.gsp_group = details.iloc[0].gsp_name

        # update database
        print("Updating database")
        session.commit()
