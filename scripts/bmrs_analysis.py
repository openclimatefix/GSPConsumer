from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
from ElexonDataPortal import api
from pvlive_api import PVLive

gsp_id = 0
# validation
start_datetime = datetime(2021, 9, 1, tzinfo=timezone.utc)
end_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)

start_datetime = datetime(2022, 9, 1, tzinfo=timezone.utc)
end_datetime = datetime(2022, 9, 10, tzinfo=timezone.utc)


# PV live
pvlive = PVLive()
gsp_yield_df: pd.DataFrame = pvlive.between(
    start=start_datetime, end=end_datetime, entity_type="gsp", entity_id=0, dataframe=True
)
gsp_yield_df.set_index("datetime_gmt", drop=True, inplace=True)


# get bmrs data
client = api.Client("52g2ac5kwwh5chc")

# one month can take a few mins to run, 1 month takes about 5 mins
solar_bmrs_all = client.get_B1440(start_datetime, end_datetime)
solar_bmrs = solar_bmrs_all
solar_bmrs = solar_bmrs[solar_bmrs["powerSystemResourceType"] == '"Solar"']
solar_bmrs = solar_bmrs[solar_bmrs["processType"] == "Day Ahead"]

solar_bmrs.index = solar_bmrs["local_datetime"]
solar_bmrs = solar_bmrs[["quantity"]]
solar_bmrs = solar_bmrs.resample("30min").mean()

# elexon periods times are at the start of the 30 mins block, pv live are at the end of the 30 min block
solar_bmrs.index = solar_bmrs.index + pd.Timedelta(minutes=30)

# get error
error = solar_bmrs.join(gsp_yield_df)
error["diff"] = error["quantity"] - error["generation_mw"]

me = error["diff"].mean()
mae = error["diff"].abs().mean()
rmse = ((error["diff"] ** 2).mean()) ** 0.5

print(f"{me=}")
print(f"{mae=}")
print(f"{rmse=}")


# plot
traces = []

# pv live
datetimes_pvlive = gsp_yield_df.index
estimates_pvlive = gsp_yield_df["generation_mw"]
pv_df = pd.DataFrame(index=datetimes_pvlive, data=estimates_pvlive, columns=["pvlive"])
traces.append(go.Scatter(x=datetimes_pvlive, y=estimates_pvlive, name="pvlive"))


# not sure why to minus 1 hour, but it does seem to line up, must be a timezone thing
datetimes_bmrs = solar_bmrs.index - pd.Timedelta(hours=1)
estimates_bmrs = solar_bmrs["quantity"]
traces.append(go.Scatter(x=datetimes_bmrs, y=estimates_bmrs, name="brms"))

# Plot

fig = go.Figure(data=traces)
fig.show(renderer="browser")
