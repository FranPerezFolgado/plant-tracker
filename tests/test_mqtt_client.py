import json

import pytest

from mqtt_client import MQTTClient, ParsedSensorData


class _Msg:
    def __init__(self, topic: str, payload: bytes):
        self.topic = topic
        self.payload = payload


def test_device_from_topic_zigbee2mqtt_prefix() -> None:
    assert MQTTClient._device_from_topic("zigbee2mqtt/living_room") == "living_room"
    assert MQTTClient._device_from_topic("zigbee2mqtt/living_room/availability") == "living_room"


def test_device_from_topic_fallback() -> None:
    assert MQTTClient._device_from_topic("some/other/topic") == "some/other/topic"


def test_extract_numeric_fields_filters_non_numeric_and_bools() -> None:
    payload = {
        "temperature": 22.5,
        "humidity": 61,
        "battery": None,
        "linkquality": "high",
        "occupied": True,  # bool is intentionally excluded
    }
    assert MQTTClient._extract_numeric_fields(payload) == {"temperature": 22.5, "humidity": 61.0}


def test_on_message_emits_parsed_sensor_data_for_valid_json() -> None:
    received: list[ParsedSensorData] = []

    def sink(parsed: ParsedSensorData) -> None:
        received.append(parsed)

    client = MQTTClient(on_sensor_data=sink)

    payload = {"temperature": 20.0, "humidity": 50, "note": "x", "dry": True}
    msg = _Msg(topic="zigbee2mqtt/my_device", payload=json.dumps(payload).encode("utf-8"))

    client._on_message(client=None, userdata=None, message=msg)

    assert len(received) == 1
    parsed = received[0]
    assert parsed.device == "my_device"
    assert parsed.topic == "zigbee2mqtt/my_device"
    assert parsed.fields == {"temperature": 20.0, "humidity": 50, "note": "x", "dry": True}
    assert parsed.received_at.tzinfo is not None


@pytest.mark.parametrize("payload_bytes", [b"not-json", b"[]", b"null"])
def test_on_message_ignores_non_object_json(payload_bytes: bytes) -> None:
    received: list[ParsedSensorData] = []

    client = MQTTClient(on_sensor_data=lambda parsed: received.append(parsed))
    msg = _Msg(topic="zigbee2mqtt/my_device", payload=payload_bytes)
    client._on_message(client=None, userdata=None, message=msg)

    assert received == []

