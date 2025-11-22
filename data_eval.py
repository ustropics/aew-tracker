import xarray as xr
import numpy as np

ds = xr.open_dataset('data/AEW_tracks_post_processed_year_1995.nc')

print(ds.AEW_strength)