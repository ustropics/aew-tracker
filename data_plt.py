# -------------------------------------------------------------
# FINAL VERSION – Clean titles exactly as you requested
# -------------------------------------------------------------

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import pandas as pd
import os
from matplotlib.collections import LineCollection


os.makedirs('figures', exist_ok=True)

# Load and clean data
ds = xr.open_dataset('data/AEW_tracks_post_processed_year_1995.nc')
if ds.time.to_index().duplicated().any():
    _, idx = np.unique(ds.time.values, return_index=True)
    ds = ds.isel(time=idx).sortby('time')

time_pd = pd.to_datetime(ds.time.values)
ds = ds.assign_coords(month=('time', time_pd.month))

lon = ds.AEW_lon_smooth
lat = ds.AEW_lat_smooth
strength = ds.AEW_strength

vmin = float(strength.min().values)
vmax = float(strength.max().values)
cmap = plt.cm.plasma_r

# ==============================================================
def plot_with_proper_title(month_num=None):
    if month_num is not None:
        month_name = pd.to_datetime(f'1995-{month_num}-01').strftime('%B')
        time_str = rf"\textbf{{Time}}: {month_name} 1995"
        mask = ds.month == month_num
    else:
        time_str = "Time: June–October 1995 (Full Season)"
        mask = slice(None)

    fig = plt.figure(figsize=(20, 14))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # --- Map setup ---
    ax.coastlines(resolution='50m', linewidth=0.8)
    ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
    ax.add_feature(cfeature.STATES, linestyle=':', alpha=0.6)
    ax.add_feature(cfeature.OCEAN, facecolor='white')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.6)
    ax.set_extent([-120, 60, -20, 60], crs=ccrs.PlateCarree())

    n_tracks = 0
    for sys in ds.system.values:
        x = lon.sel(system=sys).where(mask, drop=False).values
        y = lat.sel(system=sys).where(mask, drop=False).values
        s = strength.sel(system=sys).where(mask, drop=False).values

        valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(s))
        if not valid.any():
            continue

        x, y, s = x[valid], y[valid], s[valid]
        n_tracks += 1

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=cmap, norm=plt.Normalize(vmin, vmax),
                            linewidth=2.4, alpha=0.92, transform=ccrs.PlateCarree())
        lc.set_array(s[:-1])
        ax.add_collection(lc)

    # --- Proper figure-level title and subtitles ---
    fig.suptitle('African Easterly Wave Tracks', fontsize=24, fontweight='bold', y=0.75, x=.26)

    plt.figtext(0.125, 0.705, time_str, fontsize=15)
    #plt.figtext(0.5, 0.85, f"Count: {n_tracks} tracks",
    #            ha='center', fontsize=16, style='italic')

    # --- Colorbar ---
    cbar = plt.colorbar(lc, ax=ax, shrink=0.5, pad=0.02, aspect=25)
    cbar.set_label('AEW Strength', fontsize=13, fontweight='bold')

    # --- Gridlines ---
    gl = ax.gridlines(draw_labels=True, alpha=0.5, linestyle='--')
    gl.top_labels = gl.right_labels = False

    # --- Save ---
    if month_num is not None:
        name = pd.to_datetime(f'1995-{month_num}-01').strftime('%B')
        outfile = f'figures/AEW_tracks_strength_{name}_1995.png'
    else:
        outfile = 'figures/AEW_tracks_strength_FullSeason_1995.png'

    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved → {outfile}")

# ==============================================================
print("Creating all plots with perfect title placement...\n")
for m in [6, 7, 8, 9, 10]:
    plot_with_proper_title(m)

plot_with_proper_title(month_num=None)  # full season

print("\nDone! All 6 figures saved with clean, visible titles.")