#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
export_aew_tracks_for_leaflet.py

Export AEW tracks from 1979 to 2023 (all years) into:
  - One big interactive GeoJSON (perfect for Leaflet/Folium/Kepler.gl)
  - Optionally: one JSON per year

Features:
- One Feature per track (LineString)
- Per-point strength, month, timestamp
- Rich properties for filtering and styling
- Fully valid GeoJSON (CRS84)
"""

import xarray as xr
import numpy as np
import pandas as pd
import json
import os
from datetime import datetime

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
START_YEAR = 1979
END_YEAR   = 2023
DATA_DIR   = "data"
OUTPUT_DIR = "output"

# Output options
COMBINED_OUTPUT = f"{OUTPUT_DIR}/aew_tracks_1979_2023_interactive.json"
PER_YEAR_OUTPUT = True  # Set to False if you only want the combined file

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# Helper: process a single year's file
# ----------------------------------------------------------------------
def process_year(year):
    netcdf_file = f"{DATA_DIR}/AEW_tracks_post_processed_year_{year}.nc"
    if not os.path.exists(netcdf_file):
        print(f"Warning: Missing {netcdf_file} → skipping {year}")
        return None, year

    print(f"Loading {netcdf_file} ...")
    ds = xr.open_dataset(netcdf_file)

    # Remove duplicate times
    if ds.time.to_index().duplicated().any():
        _, idx = np.unique(ds.time.values, return_index=True)
        ds = ds.isel(time=idx).sortby('time')

    # Add month coordinate
    time_pd = pd.to_datetime(ds.time.values)
    ds = ds.assign_coords(month=('time', time_pd.month))

    lon = ds.AEW_lon_smooth
    lat = ds.AEW_lat_smooth
    strength = ds.AEW_strength

    features = []
    for sys in ds.system.values:
        x = lon.sel(system=sys).values
        y = lat.sel(system=sys).values
        s = strength.sel(system=sys).values
        t = ds.time.values

        valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(s))
        if not valid.any():
            continue

        x, y, s, t = x[valid], y[valid], s[valid], t[valid]

        coordinates = [[float(lon_val), float(lat_val)] for lon_val, lat_val in zip(x, y)]
        times_str = pd.to_datetime(t).strftime('%Y-%m-%d %H:%M').tolist()
        months = pd.to_datetime(t).month.tolist()

        point_data = [
            {"strength": float(val), "month": int(mo), "time": tm}
            for val, mo, tm in zip(s, months, times_str)
        ]

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "system_id": int(sys.values) if hasattr(sys, 'values') else str(sys),
                "year": int(year),
                "track_length_points": len(coordinates),
                "months": list(set(months)),
                "strength_min": float(s.min()),
                "strength_max": float(s.max()),
                "strength_mean": float(s.mean()),
                "point_data": point_data
            }
        }
        features.append(feature)

    print(f"  → {len(features)} tracks from {year}")
    return features, year

# ----------------------------------------------------------------------
# Main: loop over all years
# ----------------------------------------------------------------------
all_features = []

for year in range(START_YEAR, END_YEAR + 1):
    features, yr = process_year(year)
    if features:
        all_features.extend(features)

        # Optional: save per-year file
        if PER_YEAR_OUTPUT:
            per_year_json = f"{OUTPUT_DIR}/aew_tracks_{yr}_interactive.json"
            geojson_year = {
                "type": "FeatureCollection",
                "name": f"African Easterly Wave Tracks {yr}",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "features": features
            }
            with open(per_year_json, "w", encoding="utf-8") as f:
                json.dump(geojson_year, f, indent=2)
            print(f"  Saved {per_year_json}")

# ----------------------------------------------------------------------
# Save combined file (1979–2023)
# ----------------------------------------------------------------------
if all_features:
    geojson_combined = {
        "type": "FeatureCollection",
        "name": "African Easterly Wave Tracks 1979–2023",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": all_features
    }

    with open(COMBINED_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(geojson_combined, f, indent=2)

    print("\n" + "="*60)
    print(f"SUCCESS: Exported {len(all_features)} tracks (1979–2023)")
    print(f"→ Combined file: {COMBINED_OUTPUT}")
    if PER_YEAR_OUTPUT:
        print(f"→ Per-year files saved in {OUTPUT_DIR}/")
    print("Ready for Leaflet, Folium, Kepler.gl!")
    print("   • Filter by year: feature.properties.year")
    print("   • Filter by month: feature.properties.months")
    print("   • Color by strength_mean, filter by strength_min/max, etc.")
else:
    print("No data processed. Check your data files.")
