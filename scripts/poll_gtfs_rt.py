import csv
from datetime import datetime, timezone
from pathlib import Path

import requests
from google.transit import gtfs_realtime_pb2

from config import (
    DATA_DIR,
    GTFS_RT_VEHICLE_POSITIONS_URL,
    GTFS_RT_TRIP_UPDATES_URL,
)

TIMEOUT_SECONDS = 20

VEHICLE_POSITIONS_DIR = DATA_DIR / "raw" / "vehicle_positions"
TRIP_UPDATES_DIR = DATA_DIR / "raw" / "trip_updates"
VEHICLE_POSITIONS_DIR.mkdir(parents=True, exist_ok=True)
TRIP_UPDATES_DIR.mkdir(parents=True, exist_ok=True)

VEHICLE_POSITIONS_FIELDS = [
    "poll_time", "vehicle_id", "trip_id", "route_id", "latitude", "longitude",
    "current_stop_sequence", "stop_id", "current_status", "vehicle_timestamp",
]
TRIP_UPDATES_FIELDS = [
    "poll_time", "trip_id", "route_id", "stop_id", "stop_sequence",
    "arrival_delay", "arrival_time", "departure_delay", "departure_time",
    "schedule_relationship",
]


def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage:
    resp = requests.get(url, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(resp.content)
    except Exception as e:
        raise ValueError(
            f"Failed to parse feed from {url} "
            f"(status={resp.status_code}, bytes={len(resp.content)}): {e}"
        )
    return feed


def append_rows(directory: Path, fields: list, rows: list):
    """Append rows to today's CSV file, writing a header only if the file is new."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = directory / f"{today_str}.csv"
    file_is_new = not filepath.exists()

    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if file_is_new:
            writer.writeheader()
        writer.writerows(rows)


def poll_vehicle_positions(poll_time: str) -> int:
    feed = fetch_feed(GTFS_RT_VEHICLE_POSITIONS_URL)
    rows = []
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        v = entity.vehicle
        rows.append({
            "poll_time": poll_time,
            "vehicle_id": v.vehicle.id if v.HasField("vehicle") else None,
            "trip_id": v.trip.trip_id if v.HasField("trip") else None,
            "route_id": v.trip.route_id if v.HasField("trip") else None,
            "latitude": v.position.latitude if v.HasField("position") else None,
            "longitude": v.position.longitude if v.HasField("position") else None,
            "current_stop_sequence": v.current_stop_sequence if v.HasField("current_stop_sequence") else None,
            "stop_id": v.stop_id if v.HasField("stop_id") else None,
            "current_status": gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.Name(v.current_status)
                if v.HasField("current_status") else None,
            "vehicle_timestamp": v.timestamp if v.HasField("timestamp") else None,
        })

    append_rows(VEHICLE_POSITIONS_DIR, VEHICLE_POSITIONS_FIELDS, rows)
    print(f"  vehicle_positions: appended {len(rows)} rows")
    return len(rows)


def poll_trip_updates(poll_time: str) -> int:
    feed = fetch_feed(GTFS_RT_TRIP_UPDATES_URL)
    rows = []
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        tu = entity.trip_update
        trip_id = tu.trip.trip_id if tu.HasField("trip") else None
        route_id = tu.trip.route_id if tu.HasField("trip") else None

        for stu in tu.stop_time_update:
            rows.append({
                "poll_time": poll_time,
                "trip_id": trip_id,
                "route_id": route_id,
                "stop_id": stu.stop_id if stu.HasField("stop_id") else None,
                "stop_sequence": stu.stop_sequence if stu.HasField("stop_sequence") else None,
                "arrival_delay": stu.arrival.delay if stu.HasField("arrival") else None,
                "arrival_time": stu.arrival.time if stu.HasField("arrival") else None,
                "departure_delay": stu.departure.delay if stu.HasField("departure") else None,
                "departure_time": stu.departure.time if stu.HasField("departure") else None,
                "schedule_relationship":
                    gtfs_realtime_pb2.TripUpdate.StopTimeUpdate.ScheduleRelationship.Name(
                        stu.schedule_relationship
                    ) if stu.HasField("schedule_relationship") else None,
            })

    append_rows(TRIP_UPDATES_DIR, TRIP_UPDATES_FIELDS, rows)
    print(f"  trip_updates: appended {len(rows)} rows")
    return len(rows)


def main():
    poll_time = datetime.now(timezone.utc).isoformat()
    print(f"[{poll_time}] Polling SacRT GTFS-RT feeds...")

    vp_count = tu_count = 0
    try:
        vp_count = poll_vehicle_positions(poll_time)
    except Exception as e:
        print(f"  vehicle_positions poll failed, skipping: {e}")

    try:
        tu_count = poll_trip_updates(poll_time)
    except Exception as e:
        print(f"  trip_updates poll failed, skipping: {e}")

    print(f"Done. {vp_count} vehicle rows, {tu_count} trip-update rows.")


if __name__ == "__main__":
    main()