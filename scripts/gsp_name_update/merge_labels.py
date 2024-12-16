""" Merge labels """

# import the files

import pandas as pd

# importing file with new ids
new_df = pd.read_csv("GSPConsumer/gsp_name_update/gsp_new_ids.csv")
print(new_df.head())

# importing file with old ids
old_df = pd.read_csv("GSPConsumer/gsp_name_update/gsp_old_ids.csv")
print(old_df.head())


# joining them up on gsp_name to get readable name

joined_df = new_df.merge(old_df, how="left", on=["gsp_name"])
print(joined_df.head())

# dropping duplicates from the joined file
joined_df.drop_duplicates(subset=["gsp_id_x"], keep="first", inplace=True)
print("subset removed")


joined_df.to_csv("GSPConsumer/gsp_name_update/gsp_new_ids_and_names.csv")
print(joined_df.head())


print("finished")
