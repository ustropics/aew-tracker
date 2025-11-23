#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
export_aew_tracks_for_leaflet.py
Now with Tropical Cyclone genesis information!

Exports AEW tracks (1979–2023) → interactive GeoJSON with:
  • TC_name
  • TC_genesis_time
  • developed_into_tc (boolean) → perfect for filtering/styling
"""

import xarray as xr
import numpy as np
import pandas as pd
import json
import os

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
START_YEAR = 1979
END_YEAR = 2023
DATA_DIR = "data"
OUTPUT_DIR = "output"

# Output options
COMBINED_OUTPUT = f"{OUTPUT_DIR}/aew_tracks_1979_2023_interactive.json"
PER_YEAR_OUTPUT = True  # Set to False if you only want the big combined file

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

    # Remove duplicate times (safety)
    if ds.time.to_index().duplicated().any():
        _, idx = np.unique(ds.time.values, return_index=True)
        ds = ds.isel(time=idx).sortby('time')

    # Add month as coordinate
    time_pd = pd.to_datetime(ds.time.values)
    ds = ds.assign_coords(month=('time', time_pd.month))

    lon = ds.AEW_lon_smooth
    lat = ds.AEW_lat_smooth
    strength = ds.AEW_strength

    features = []
    for sys in ds.system.values:
        # Extract track data
        x = lon.sel(system=sys).values
        y = lat.sel(system=sys).values
        s = strength.sel(system=sys).values
        t = ds.time.values

        # Mask invalid points
        valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(s))
        if not valid.any():
            continue

        x, y, s, t = x[valid], y[valid], s[valid], t[valid]

        coordinates = [[float(lon_val), float(lat_val)]
                       for lon_val, lat_val in zip(x, y)]
        times_str = pd.to_datetime(t).strftime('%Y-%m-%d %H:%M').tolist()
        months = pd.to_datetime(t).month.tolist()

        point_data = [
            {"strength": float(val), "month": int(mo), "time": tm}
            for val, mo, tm in zip(s, months, times_str)
        ]

        # ──────────────────────────────
        # TC Genesis Information
        # ──────────────────────────────
        tc_name_raw = ds.TC_name.sel(system=sys).values
        tc_gen_time_raw = ds.TC_gen_time.sel(system=sys).values

        # Clean TC name (remove padding, handle missing/unnamed)
        tc_name = str(tc_name_raw).strip()
        if tc_name == '' or tc_name == 'nan' or pd.isna(tc_name_raw):
            tc_name = None

        # Handle genesis time
        if pd.isna(tc_gen_time_raw):
            developed_into_tc = False
            tc_genesis_time = None
        else:
            tc_gen_dt = pd.to_datetime(tc_gen_time_raw)
            tc_genesis_time = tc_gen_dt.strftime('%Y-%m-%d %H:%M')
            developed_into_tc = True

        # ──────────────────────────────
        # Build Feature
        # ──────────────────────────────
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "system_id": int(sys.values) if hasattr(sys, 'values') else int(sys),
                "year": int(year),
                "track_length_points": len(coordinates),
                "months": list(set(months)),
                "strength_min": float(s.min()),
                "strength_max": float(s.max()),
                "strength_mean": float(s.mean()),
                "point_data": point_data,

                # NEW: Tropical Cyclone info
                "developed_into_tc": developed_into_tc,
                "tc_name": tc_name,
                "tc_genesis_time": tc_genesis_time,
            }
        }
        features.append(feature)

    print(f"  → {len(features)} tracks from {year} (including TC precursors)")
    return features, year


# ----------------------------------------------------------------------
# Main: loop over all years
# ----------------------------------------------------------------------
all_features = []

for year in range(START_YEAR, END_YEAR + 1):
    features, yr = process_year(year)
    if features:
        all_features.extend(features)

        # Optional: save per-year GeoJSON
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
# Save combined 1979–2023 file
# ----------------------------------------------------------------------
if all_features:
    geojson_combined = {
        "type": "FeatureCollection",
        "name": "African Easterly Wave Tracks 1979–2023 (with TC Genesis)",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": all_features
    }

    with open(COMBINED_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(geojson_combined, f, indent=2)

    # Summary
    tc_count = sum(
        1 for f in all_features if f["properties"]["developed_into_tc"])
    print("\n" + "="*70)
    print(f"SUCCESS! Exported {len(all_features)} AEW tracks (1979–2023)")
    print(f"→ {tc_count} of them developed into named Tropical Cyclones")
    print(f"→ Combined file: {COMBINED_OUTPUT}")
    if PER_YEAR_OUTPUT:
        print(f"→ Per-year files in: {OUTPUT_DIR}/")
    print("\nReady for Leaflet / Folium / Kepler.gl!")
    print("   • Filter TCs:   feature.properties.developed_into_tc === true")
    print("   • Show name:    feature.properties.tc_name")
    print("   • Genesis time: feature.properties.tc_genesis_time")
    print("="*70)
else:
    print("No data processed. Check your input files and paths.")
