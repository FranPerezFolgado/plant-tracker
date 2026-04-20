from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

import main


class _FakeInflux:
    def list_devices(self):
        return ["devA", "devB"]

    def latest_fields(self, device: str):
        if device == "devA":
            return datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), {
                "battery": 75,
                "dry": True,
                "humidity": 59,
                "soil_moisture": 0,
                "temperature": 24.7,
                "temperature_unit": "celsius",
            }
        return None, {}


class _FakeState:
    def __init__(self) -> None:
        self.influx = _FakeInflux()


def test_get_devices_returns_list() -> None:
    main.app.state.state = _FakeState()
    client = TestClient(main.app)

    res = client.get("/devices")
    assert res.status_code == 200
    assert res.json() == {"devices": ["devA", "devB"]}


def test_get_device_latest_returns_time_and_fields() -> None:
    main.app.state.state = _FakeState()
    client = TestClient(main.app)

    res = client.get("/devices/devA/latest")
    assert res.status_code == 200
    body = res.json()
    assert body["device"] == "devA"
    assert body["time"] == "2026-01-01T00:00:00+00:00"
    assert body["fields"]["temperature"] == 24.7
    assert body["fields"]["dry"] is True
    assert body["fields"]["temperature_unit"] == "celsius"


def test_get_devices_latest_returns_all() -> None:
    main.app.state.state = _FakeState()
    client = TestClient(main.app)

    res = client.get("/devices/latest")
    assert res.status_code == 200
    body = res.json()
    assert body["devices"][0]["device"] == "devA"
    assert body["devices"][1]["device"] == "devB"

