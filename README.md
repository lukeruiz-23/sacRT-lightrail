# SacRT Light Rail Performance & Efficiency

An end-to-end data science project measuring real-world on-time performance,
headway consistency, and delay patterns on Sacramento Regional Transit's
light rail system, using SacRT's live GTFS-Realtime feed compared against
its published schedule (static GTFS). Showing a model to predict delays and
a data backed recommendation at the end.

## Status
Data collection phase.

## Project structure
```
scripts/
  config.py            Feed URLs and file paths
  fetch_static_gtfs.py Downloads the schedule + filters to light rail only
  init_db.py            Creates the SQLite schema
  poll_gtfs_rt.py       Polls the live feed once, stores a snapshot
data/
  static_gtfs/          Downloaded schedule data (gitignored, regenerate locally)
  sacrt_lightrail.db    SQLite DB accumulating real-time snapshots
.github/workflows/
  poll.yml              GitHub Actions cron job: polls the feed every 5 min
notebooks/               Analysis notebooks (added in the analysis phase)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. **Download the static schedule and identify light rail routes:**
   ```bash
   cd scripts
   python fetch_static_gtfs.py
   ```
   This filters SacRT's combined bus+rail feed down to just light rail
   (`route_type == 0`) and saves `lr_routes.csv`, `lr_trips.csv`,
   `lr_stops.csv`, `lr_stop_times.csv` for later joins.

2. **Initialize the database:**
   ```bash
   python init_db.py
   ```

3. **Test a single poll:**
   ```bash
   python poll_gtfs_rt.py
   ```
   You should see row counts printed for both vehicle positions and trip
   updates. If this returns 0 rows repeatedly, check that the feed is up
   at https://www.sacrt.com/transit-data-portal/.

## Continuous collection

The included GitHub Actions workflow (`.github/workflows/poll.yml`) polls
the feed every 5 minutes and commits the growing SQLite database back to
the repo — no server required. To enable it:

1. Push this repo to GitHub.
2. Go to the repo's **Settings → Actions → General → Workflow permissions**
   and set it to "Read and write permissions" (needed so the workflow can
   commit the DB back).
3. The workflow will start running on its schedule automatically. You can
   also trigger it manually from the **Actions** tab (`workflow_dispatch`).

Let this run for 2–4 weeks to get a meaningful sample across different
days of week and times of day.

## Data sources
- **Static GTFS (schedule):** `https://apps.sacrt.com/gtfs/srtd/google_transit.zip`
- **GTFS-RT vehicle positions:** `https://bustime.sacrt.com/gtfsrt/vehicles`
- **GTFS-RT trip updates:** `https://bustime.sacrt.com/gtfsrt/trips`
- **GTFS-RT alerts:** `https://bustime.sacrt.com/gtfsrt/alerts`

Data is provided by SacRT on an "as-is" basis per their
[data portal terms](https://www.sacrt.com/transit-data-portal/).

## Roadmap
- [x] Confirm live feed access and set up polling pipeline
- [ In Progress ] Collect 2-4 weeks of real-time data
- [ ] Compute on-time performance, headway variance, and delay hotspots by line/segment
- [ ] Pull weather data (NOAA) as a feature source
- [ ] Train delay-prediction model (baseline regression → XGBoost), compare + feature importance
- [ ] Build Streamlit dashboard, deploy to Streamlit Community Cloud
- [ ] Write up findings and a concrete recommendation
