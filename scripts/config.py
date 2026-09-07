"""Central configuration: feed URLs and file paths."""
from pathlib import Path

# --- SacRT feed URLs (confirmed live as of Sep 2026) ---
STATIC_GTFS_URL = "https://apps.sacrt.com/gtfs/srtd/google_transit.zip"

GTFS_RT_VEHICLE_POSITIONS_URL = "https://bustime.sacrt.com/gtfsrt/vehicles"
GTFS_RT_TRIP_UPDATES_URL = "https://bustime.sacrt.com/gtfsrt/trips"
GTFS_RT_ALERTS_URL = "https://bustime.sacrt.com/gtfsrt/alerts"

# --- Light rail identification ---
# In GTFS, route_type 0 = Tram/Streetcar/Light rail.
# SacRT's feed mixes light rail + bus in one static feed, so we filter on this.
LIGHT_RAIL_ROUTE_TYPE = 0

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATIC_GTFS_DIR = DATA_DIR / "static_gtfs"
DB_PATH = DATA_DIR / "sacrt_lightrail.db"

DATA_DIR.mkdir(exist_ok=True)
STATIC_GTFS_DIR.mkdir(exist_ok=True)
