# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Plant Tracker collects environmental sensor readings from Zigbee devices via Zigbee2MQTT → MQTT → InfluxDB v2, and exposes them through a FastAPI REST API. The intended deployment target is ZimaOS (home server).

## Commands

```bash
# Install dependencies (Python 3.12+)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the API locally (requires env vars or a .env file)
PYTHONPATH=app uvicorn main:app --reload --app-dir app

# Run all tests
pytest

# Run a single test file
pytest tests/test_api_endpoints.py

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Start infrastructure (Mosquitto + InfluxDB) without the app
docker compose up mosquitto influxdb -d

# Start everything including the app container
docker compose up --build
```

## Environment

Copy `.env.example` to `.env` and fill in values. The key variables:

| Variable | Default | Purpose |
|---|---|---|
| `MQTT_BROKER_HOST` | `mosquitto` | Hostname of the MQTT broker |
| `MQTT_TOPIC` | `zigbee2mqtt/#` | Topic wildcard to subscribe |
| `INFLUXDB_URL` | `http://influxdb:8086` | InfluxDB v2 URL |
| `INFLUXDB_TOKEN` | `changeme-token` | Auth token (set in InfluxDB UI) |
| `INFLUXDB_ORG` | `plant-tracker` | InfluxDB org |
| `INFLUXDB_BUCKET` | `sensors` | Target bucket |

When running locally (not in Docker), point `MQTT_BROKER_HOST` and `INFLUXDB_URL` to `localhost`.

## Architecture

```
Zigbee device
    ↓ (Zigbee2MQTT bridge)
Mosquitto (MQTT broker, port 1883)
    ↓
MQTTClient (paho-mqtt, background thread)
    ↓ on_sensor_data callback
InfluxManager (influxdb-client, SYNCHRONOUS writes)
    ↓
InfluxDB v2 (port 8086, measurement: zigbee_sensor)
    ↑
FastAPI (uvicorn, port 8000) → REST endpoints
```

All three `app/` modules are loaded at startup via the FastAPI `lifespan` context manager in `main.py`. `AppState` holds references to both live service objects and is stored in `app.state.state`.

**Data flow:** MQTT messages arrive on `zigbee2mqtt/<friendlyName>`. `MQTTClient._on_message` decodes the JSON payload, extracts only numeric fields (booleans are excluded), and calls the `on_sensor_data` callback which writes a `Point` to InfluxDB with tags `device` and `topic`.

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | MQTT + InfluxDB connection status |
| GET | `/devices` | List all devices seen in the last 30 days |
| GET | `/devices/latest` | Latest reading for every device |
| GET | `/devices/{device}/latest` | Latest reading for a specific device |

Interactive docs: `http://localhost:8000/docs`

## Testing approach

Tests live in `tests/`. `conftest.py` adds `app/` to `sys.path` so imports mirror the Docker runtime (`PYTHONPATH=app`).

API tests in `test_api_endpoints.py` inject a fake `AppState` directly into `app.state.state` — no lifespan runs, no real network connections needed. Follow the same fake-injection pattern for new endpoint tests.

Unit tests for `MQTTClient` and `InfluxManager` use `unittest.mock.patch` for network calls. Keep new unit tests focused on pure parsing logic or Flux query construction.

## HTTP request file

`requests.http` at the project root can be run directly in Cursor/VS Code REST Client to exercise the live API.
