from influx_manager import InfluxManager


class _FakeWriteApi:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def write(self, **kwargs):
        self.calls.append(kwargs)


def test_write_sensor_data_writes_point_to_configured_bucket_and_org(monkeypatch) -> None:
    mgr = InfluxManager(url="http://localhost:8086", token="t", org="o", bucket="b")

    fake = _FakeWriteApi()
    monkeypatch.setattr(mgr, "write_api", fake)

    mgr.write_sensor_data(
        measurement="zigbee_sensor",
        tags={"device": "dev1", "topic": "zigbee2mqtt/dev1"},
        fields={"temperature": 21.5, "humidity": 60.0},
    )

    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["bucket"] == "b"
    assert call["org"] == "o"

    record = call["record"]
    lp = record.to_line_protocol()
    assert lp.startswith("zigbee_sensor")
    assert "device=dev1" in lp
    assert "topic=zigbee2mqtt/dev1" in lp
    assert "temperature=21.5" in lp
    assert "humidity=60" in lp or "humidity=60.0" in lp

