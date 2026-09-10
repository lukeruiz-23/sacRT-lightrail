import os
import time
import pandas as pd
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()
NOAA_TOKEN = os.getenv("NOAA_TOKEN")

BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"
STATION_ID = "GHCND:USW00023232"  # Sacramento Executive Airport

def fetch_daily_weather (start_date: str, end_date: str) -> list[dict]:
    """Fetch daily TMAX, TMIN, PRCP for the station between two dates (YYYY-MM-DD)."""
    headers = {"token": NOAA_TOKEN}
    params={
        "datasetid": "GHCND",
        "stationid": STATION_ID,
        "startdate": start_date,
        "enddate" : end_date,
        "datatypeid": ["TMAX", "TMIN", "PRCP"],
        "units" : "standard",
        "limit" : 1000,
    }
    resp = requests.get(f"{BASE_URL}/data", headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])

def fetch_weather_range(start_date: str, end_date: str, chunk_days: int = 30) -> pd.DataFrame:
    """Fetch daily weather across a potentially long date range by
    breaking it into smaller chunks, respecting NOAA's rate limit."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    all_results = []
    chunk_start = start

    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=chunk_days - 1), end)

        print(f"  Fetching {chunk_start} to {chunk_end}...")
        results = fetch_daily_weather(chunk_start.isoformat(), chunk_end.isoformat())
        all_results.extend(results)

        chunk_start = chunk_end + timedelta(days=1)
        time.sleep(0.25)  # stay well under 5 requests/second

    return reshape_to_daily(all_results)

def reshape_to_daily(results: list[dict]) -> pd.DataFrame:
    """Turn NOAA's long-format records (one row per date+datatype) into
    one row per date with tmax/tmin/prcp as columns."""
    if not results:
        return pd.DataFrame(columns=["date", "tmax", "tmin", "prcp"])

    df = pd.DataFrame(results)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    wide = df.pivot_table(
        index="date",
        columns="datatype",
        values="value",
        aggfunc="first",
    ).reset_index()

    wide.columns.name = None
    wide = wide.rename(columns={"TMAX": "tmax", "TMIN": "tmin", "PRCP": "prcp"})
    return wide

if __name__ == "__main__":
    if not NOAA_TOKEN:
        raise SystemExit("NOAA_TOKEN not found")

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=60)  # test with 2 months

    print(f"Fetching weather from {start} to {end} for station {STATION_ID}...")
    daily = fetch_weather_range(start.isoformat(), end.isoformat())
    print(daily)
    print(f"\n{len(daily)} days of weather data.")
    output_path = "data/weather_sacramento.csv"
    daily.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
