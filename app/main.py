"""
main.py — Entry point for the Plant Tracker FastAPI application.

Responsibilities:
- Initialise the FastAPI app.
- Register routers / endpoints.
- Start background services (MQTT client, InfluxDB connection) on startup.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI

from influx_manager import InfluxManager
from mqtt_client import MQTTClient, ParsedSensorData


class AppState:
    def __init__(self, influx: InfluxManager, mqtt: MQTTClient) -> None:
        self.influx = influx
        self.mqtt = mqtt


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifecycle using the recommended lifespan context manager.

    Code before the ``yield`` runs on startup; code after runs on shutdown.
    """
    # ── Startup ───────────────────────────────────────────────────────────
    influx = InfluxManager()

    def on_sensor_data(parsed: ParsedSensorData) -> None:
        influx.write_sensor_data(
            measurement="zigbee_sensor",
            tags={"device": parsed.device, "topic": parsed.topic},
            fields=parsed.fields,
        )

    mqtt = MQTTClient(on_sensor_data=on_sensor_data)
    mqtt.connect()

    app.state.state = AppState(influx=influx, mqtt=mqtt)

    yield  # Application is running

    # ── Shutdown ──────────────────────────────────────────────────────────
    try:
        state: AppState | None = getattr(app.state, "state", None)
        if state is not None:
            state.mqtt.disconnect()
            state.influx.close()
    finally:
        app.state.state = None


app = FastAPI(
    title="Plant Tracker API",
    description="Exposes Zigbee sensor data collected via MQTT and stored in InfluxDB.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health-check endpoint.

    Returns a simple JSON payload indicating that the service is running.
    Extend this endpoint to also report the status of MQTT and InfluxDB
    connections when the logic is implemented.
    """
    state: AppState | None = getattr(app.state, "state", None)
    return {
        "status": "ok",
        "mqtt_connected": bool(state and state.mqtt.is_connected),
        "influx_configured": bool(state and state.influx.token),
        "influx_bucket": getattr(state.influx, "bucket", None) if state else None,
        "influx_org": getattr(state.influx, "org", None) if state else None,
    }


@app.get("/devices", tags=["Devices"])
async def list_devices():
    state: AppState | None = getattr(app.state, "state", None)
    if state is None:
        return {"devices": []}
    return {"devices": state.influx.list_devices()}


@app.get("/devices/{device}/latest", tags=["Devices"])
async def latest_device(device: str):
    state: AppState | None = getattr(app.state, "state", None)
    if state is None:
        return {"device": device, "time": None, "fields": {}}

    time, fields = state.influx.latest_fields(device=device)
    return {"device": device, "time": _dt_to_iso(time), "fields": fields}


@app.get("/devices/latest", tags=["Devices"])
async def latest_all_devices():
    state: AppState | None = getattr(app.state, "state", None)
    if state is None:
        return {"devices": []}

    devices = state.influx.list_devices()
    latest: list[dict[str, Any]] = []
    for device in devices:
        time, fields = state.influx.latest_fields(device=device)
        latest.append({"device": device, "time": _dt_to_iso(time), "fields": fields})
    return {"devices": latest}


def _dt_to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()
