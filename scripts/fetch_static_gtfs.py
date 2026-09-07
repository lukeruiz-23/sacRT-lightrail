"""
Download SacRT's static GTFS feed (schedule data) and identify which
routes/trips/stops belong to light rail (as opposed to bus).

Run this once at the start of the project, and again if you suspect
SacRT has published a schedule change during your collection window.
"""
import io
import zipfile

import pandas as pd
import requests

from config import STATIC_GTFS_URL, STATIC_GTFS_DIR, LIGHT_RAIL_ROUTE_TYPE


def download_and_extract():
    print(f"Downloading static GTFS from {STATIC_GTFS_URL} ...")
    resp = requests.get(STATIC_GTFS_URL, timeout=60)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        z.extractall(STATIC_GTFS_DIR)
    print(f"Extracted GTFS files to {STATIC_GTFS_DIR}")


def summarize_light_rail():
    routes = pd.read_csv(STATIC_GTFS_DIR / "routes.txt")
    trips = pd.read_csv(STATIC_GTFS_DIR / "trips.txt")
    stops = pd.read_csv(STATIC_GTFS_DIR / "stops.txt")
    stop_times = pd.read_csv(STATIC_GTFS_DIR / "stop_times.txt")

    lr_routes = routes[routes["route_type"] == LIGHT_RAIL_ROUTE_TYPE]
    print("\nLight rail routes found:")
    cols = [c for c in ["route_id", "route_short_name", "route_long_name"] if c in lr_routes.columns]
    print(lr_routes[cols].to_string(index=False))

    lr_trips = trips[trips["route_id"].isin(lr_routes["route_id"])]
    lr_stop_times = stop_times[stop_times["trip_id"].isin(lr_trips["trip_id"])]
    lr_stop_ids = lr_stop_times["stop_id"].unique()
    lr_stops = stops[stops["stop_id"].isin(lr_stop_ids)]

    print(f"\n{len(lr_routes)} light rail routes, {len(lr_trips)} trips, "
          f"{len(lr_stops)} stops in the static schedule.")

    # Save filtered light-rail-only tables for easy reuse later.
    lr_routes.to_csv(STATIC_GTFS_DIR / "lr_routes.csv", index=False)
    lr_trips.to_csv(STATIC_GTFS_DIR / "lr_trips.csv", index=False)
    lr_stops.to_csv(STATIC_GTFS_DIR / "lr_stops.csv", index=False)
    lr_stop_times.to_csv(STATIC_GTFS_DIR / "lr_stop_times.csv", index=False)
    print(f"Saved filtered light-rail tables (lr_*.csv) to {STATIC_GTFS_DIR}")


if __name__ == "__main__":
    download_and_extract()
    summarize_light_rail()
