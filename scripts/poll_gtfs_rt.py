"""
Poll SacRT's GTFS-Realtime feeds (vehicle positions + trip updates) ONCE
and append a snapshot to the SQLite database.

Design note: this script is meant to be run repeatedly on a schedule
(cron, GitHub Actions, etc.) rather than looping internally — that keeps
each run stateless and simple to debug, and makes it trivial to see
exactly when/why a given poll failed.

Usage:
    python poll_gtfs_rt.py
"""
import sqlite3
from datetime import datetime, timezone

import requests
from google.transit import gtfs_realtime_pb2

from config import (
    DB_PATH,
    GTFS_RT_VEHICLE_POSITIONS_URL,
    GTFS_RT_TRIP_UPDATES_URL,
)

TIMEOUT_SECONDS = 20


def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage:
    resp = requests.get(url, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def poll_vehicle_positions(conn, poll_time: str):
    feed = fetch_feed(GTFS_RT_VEHICLE_POSITIONS_URL)
    rows = []
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        v = entity.vehicle
        rows.append((
            poll_time,
            v.vehicle.id if v.HasField("vehicle") else None,
            v.trip.trip_id if v.HasField("trip") else None,
            v.trip.route_id if v.HasField("trip") else None,
            v.position.latitude if v.HasField("position") else None,
            v.position.longitude if v.HasField("position") else None,
            v.current_stop_sequence if v.HasField("current_stop_sequence") else None,
            v.stop_id if v.HasField("stop_id") else None,
            gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.Name(v.current_status)
                if v.HasField("current_status") else None,
            v.timestamp if v.HasField("timestamp") else None,
        ))

    conn.executemany(
        """INSERT INTO vehicle_positions
           (poll_time, vehicle_id, trip_id, route_id, latitude, longitude,
            current_stop_sequence, stop_id, current_status, vehicle_timestamp)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    print(f"  vehicle_positions: inserted {len(rows)} rows")
    return len(rows)


def poll_trip_updates(conn, poll_time: str):
    feed = fetch_feed(GTFS_RT_TRIP_UPDATES_URL)
    rows = []
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        tu = entity.trip_update
        trip_id = tu.trip.trip_id if tu.HasField("trip") else None
        route_id = tu.trip.route_id if tu.HasField("trip") else None

        for stu in tu.stop_time_update:
            arrival_delay = stu.arrival.delay if stu.HasField("arrival") else None
            arrival_time = stu.arrival.time if stu.HasField("arrival") else None
            departure_delay = stu.departure.delay if stu.HasField("departure") else None
            departure_time = stu.departure.time if stu.HasField("departure") else None
            sched_rel = (
                gtfs_realtime_pb2.TripUpdate.StopTimeUpdate.ScheduleRelationship.Name(
                    stu.schedule_relationship
                )
                if stu.HasField("schedule_relationship") else None
            )
            rows.append((
                poll_time, trip_id, route_id,
                stu.stop_id if stu.HasField("stop_id") else None,
                stu.stop_sequence if stu.HasField("stop_sequence") else None,
                arrival_delay, arrival_time,
                departure_delay, departure_time,
                sched_rel,
            ))

    conn.executemany(
        """INSERT INTO trip_updates
           (poll_time, trip_id, route_id, stop_id, stop_sequence,
            arrival_delay, arrival_time, departure_delay, departure_time,
            schedule_relationship)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    print(f"  trip_updates: inserted {len(rows)} rows")
    return len(rows)


def main():
    poll_time = datetime.now(timezone.utc).isoformat()
    print(f"[{poll_time}] Polling SacRT GTFS-RT feeds...")

    conn = sqlite3.connect(DB_PATH)
    try:
        vp_count = poll_vehicle_positions(conn, poll_time)
        tu_count = poll_trip_updates(conn, poll_time)
        conn.commit()
        print(f"Done. {vp_count} vehicle rows, {tu_count} trip-update rows.")
    except requests.RequestException as e:
        print(f"Feed request failed: {e}")
    except Exception as e:
        print(f"Unexpected error during poll: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
