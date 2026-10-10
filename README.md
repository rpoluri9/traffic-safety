# Traffic Safety Monitoring System

A full-stack driving-safety monitoring app built with **Python** and **FastAPI**.
Vehicles stream telemetry (speed, heading, GPS, signal state, phone use, alcohol
level, seatbelt status); a **rules engine** evaluates every reading against fixed
thresholds and records violations — overspeeding, red-light crossing, wrong-way
driving, phone use while driving, drunk driving, and missing seatbelts. A
dashboard shows live stats, charts, driver safety scores, and trip routes on a map.

> **Rules-based detection — no AI/ML.** Every violation fires from a plain
> threshold comparison in `app/core/rules.py` (e.g. speed > limit, BAC > 0.08).
> There are no models, no training data, and no predictions.

## Features

- **Speed monitoring** — overspeed violation graded by margin over the limit
  (≤10 km/h MEDIUM, ≤25 HIGH, above CRITICAL)
- **Signal crossing** — red-light violation when crossing an intersection on red
- **Wrong-way driving** — heading more than 90° off the road direction (HIGH)
- **Mobile phone use** — phone in use while the vehicle is moving (MEDIUM)
- **Drunk driving** — alcohol level above 0.08 BAC → CRITICAL alert
- **Seatbelt safety** — seatbelt off while moving → MEDIUM violation
- **Navigation** — trips with pickup → drop-off, route waypoints drawn on a
  Leaflet map
- **Safety scores** — per driver, 100 minus weighted penalties
  (CRITICAL −25, HIGH −15, MEDIUM −8, LOW −3)
- **Alerts feed** — HIGH/CRITICAL violations raise alerts; acknowledge them
- **Simulate trip** — one click streams scripted telemetry that triggers
  violations so the demo comes alive
- **26 automated tests** with pytest

## Tech Stack

| Layer      | Technology                                              |
|------------|---------------------------------------------------------|
| API        | FastAPI, Pydantic v2                                    |
| Frontend   | Jinja2 templates, Chart.js 4, Leaflet 1.9 (CDN)         |
| Database   | SQLite (dev/tests), PostgreSQL (prod), SQLAlchemy 2.0   |
| Auth       | API key (`X-API-Key` header)                             |
| Rules      | Pure-Python threshold engine (`app/core/rules.py`)      |
| Tests      | pytest, FastAPI TestClient                               |
| Deploy     | Docker, Docker Compose                                   |

## Project Structure

```
traffic-safety/
├── app/
│   ├── main.py              # App factory, router wiring, static files
│   ├── core/
│   │   ├── config.py        # Settings from environment / .env
│   │   ├── security.py      # API-key auth
│   │   └── rules.py         # Rules engine (thresholds — no ML)
│   ├── db/
│   │   ├── base.py          # SQLAlchemy declarative base
│   │   └── session.py       # Engine, session factory, get_db
│   ├── models/              # Driver, Vehicle, Trip, Violation, Alert
│   ├── schemas/             # Pydantic request/response schemas
│   ├── api/v1/
│   │   ├── drivers.py       # Driver CRUD (+ safety scores)
│   │   ├── vehicles.py      # Vehicle CRUD
│   │   ├── trips.py         # Trips: create, start, complete, route
│   │   ├── telemetry.py     # POST /telemetry → rules → violations+alerts
│   │   ├── violations.py    # Filterable violation list
│   │   ├── alerts.py        # Alert feed + acknowledge
│   │   ├── dashboard.py     # Stats + safety-score endpoints
│   │   └── pages.py         # HTML dashboard pages
│   ├── templates/           # dashboard, drivers, trips, trip map, violations
│   └── static/              # style.css
├── images/                  # architecture, data model, violation flow diagrams
├── tests/                   # 26 end-to-end tests
├── seed.py                  # Demo drivers, vehicles, trips, violations
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
docker compose exec api python seed.py
```

Open http://localhost:8000 — the dashboard, drivers, trips, and violations pages
are public for the demo. The JSON API needs the key from `.env`:

```bash
curl -H "X-API-Key: demo-key-change-me" http://localhost:8000/api/v1/drivers
```

## Quick Start (local)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | /api/v1/drivers | Create driver |
| GET    | /api/v1/drivers | List drivers (with safety scores) |
| GET/PUT/DELETE | /api/v1/drivers/{id} | Driver detail / update / delete |
| POST   | /api/v1/vehicles | Create vehicle |
| GET    | /api/v1/vehicles | List vehicles |
| POST   | /api/v1/trips | Create trip (pickup → drop-off, waypoints auto-built) |
| POST   | /api/v1/trips/{id}/start | Start trip |
| POST   | /api/v1/trips/{id}/complete | Complete trip |
| POST   | /api/v1/telemetry | Submit telemetry → rules engine → violations + alerts |
| GET    | /api/v1/violations?type=&severity=&driver_id= | Filter violations |
| GET    | /api/v1/alerts | Alert feed |
| POST   | /api/v1/alerts/{id}/acknowledge | Acknowledge alert |
| GET    | /api/v1/dashboard/stats | Dashboard statistics |
| GET    | /api/v1/drivers/{id}/safety-score | Driver safety score |

### Telemetry example

```bash
curl -X POST http://localhost:8000/api/v1/telemetry \
  -H "X-API-Key: demo-key-change-me" -H "Content-Type: application/json" \
  -d '{"driver_id":1,"vehicle_id":1,"speed":72,"speed_limit":50,
       "heading":90,"road_direction":90,"signal_state":"green",
       "at_intersection":false,"phone_in_use":false,
       "alcohol_level":0.0,"seatbelt_on":true,"lat":42.36,"lng":-71.05}'
# → {"violations":[{"type":"OVERSPEED","severity":"HIGH",...}],"alerts":[...]}
```

## Rules reference

| Violation | Fires when | Severity |
|-----------|-----------|----------|
| OVERSPEED | speed > speed_limit | margin ≤10 MEDIUM, ≤25 HIGH, else CRITICAL |
| SIGNAL_CROSS | red signal + at intersection + speed > 5 km/h | HIGH |
| WRONG_WAY | heading >90° off road direction + speed > 10 km/h | HIGH |
| MOBILE_USE | phone in use + speed > 5 km/h | MEDIUM |
| DRUNK_DRIVE | alcohol_level > 0.08 BAC | CRITICAL |
| NO_SEATBELT | seatbelt off + speed > 10 km/h | MEDIUM |

## Tests

```bash
pytest tests/ -q
# 26 passed
```
