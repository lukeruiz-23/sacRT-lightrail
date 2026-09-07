"""Create the SQLite schema used to store polled GTFS-RT snapshots."""
import sqlite3

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicle_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_time TEXT NOT NULL,       -- UTC timestamp when we polled
    vehicle_id TEXT,
    trip_id TEXT,
    route_id TEXT,
    latitude REAL,
    longitude REAL,
    current_stop_sequence INTEGER,
    stop_id TEXT,
    current_status TEXT,           -- IN_TRANSIT_TO / STOPPED_AT / INCOMING_AT
    vehicle_timestamp INTEGER      -- epoch seconds reported by the feed itself
);

CREATE TABLE IF NOT EXISTS trip_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_time TEXT NOT NULL,
    trip_id TEXT,
    route_id TEXT,
    stop_id TEXT,
    stop_sequence INTEGER,
    arrival_delay INTEGER,         -- seconds; positive = late
    arrival_time INTEGER,          -- epoch seconds, predicted/actual
    departure_delay INTEGER,
    departure_time INTEGER,
    schedule_relationship TEXT
);

CREATE INDEX IF NOT EXISTS idx_vp_trip ON vehicle_positions(trip_id);
CREATE INDEX IF NOT EXISTS idx_vp_time ON vehicle_positions(poll_time);
CREATE INDEX IF NOT EXISTS idx_tu_trip_stop ON trip_updates(trip_id, stop_id);
CREATE INDEX IF NOT EXISTS idx_tu_time ON trip_updates(poll_time);
"""

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Initialized database at {DB_PATH}")
