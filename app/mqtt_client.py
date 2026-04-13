"""
mqtt_client.py — MQTT client for receiving Zigbee sensor data.

Responsibilities:
- Connect to the Mosquitto broker.
- Subscribe to the configured topic(s).
- Parse incoming messages and forward them to the InfluxDB manager.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ParsedSensorData:
    device: str
    topic: str
    received_at: datetime
    fields: Mapping[str, float]


class MQTTClient:
    """Manages the connection to the MQTT broker and message handling."""

    def __init__(
        self,
        broker_host: str = os.getenv("MQTT_BROKER_HOST", "mosquitto"),
        broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883")),
        topic: str = os.getenv("MQTT_TOPIC", "zigbee2mqtt/#"),
        on_sensor_data: Callable[[ParsedSensorData], None] | None = None,
    ):
        """
        Initialise the MQTT client with broker connection parameters.

        Args:
            broker_host: Hostname or IP address of the MQTT broker.
            broker_port: Port of the MQTT broker (default 1883).
            topic: Topic pattern to subscribe to (supports wildcards).
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self._on_sensor_data = on_sensor_data

        self._connected = False
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def connect(self) -> None:
        """
        Establish a connection to the MQTT broker and start the network loop.
        """
        logger.info(
            "Connecting to MQTT broker %s:%s (topic=%s)",
            self.broker_host,
            self.broker_port,
            self.topic,
        )
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()

    def disconnect(self) -> None:
        """
        Stop the network loop and disconnect from the broker cleanly.
        """
        try:
            self.client.loop_stop()
        finally:
            self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc: int) -> None:
        """
        Callback executed when the client connects to the broker.

        Args:
            client: The MQTT client instance.
            userdata: Private user data (unused).
            flags: Response flags from the broker.
            rc: Connection result code (0 = success).
        """
        if rc == 0:
            self._connected = True
            logger.info("Connected to MQTT broker (rc=%s). Subscribing to %s", rc, self.topic)
            client.subscribe(self.topic)
            return

        self._connected = False
        logger.error("Failed to connect to MQTT broker (rc=%s)", rc)

    def _on_message(self, client, userdata, message) -> None:
        """
        Callback executed for every message received on a subscribed topic.

        Args:
            client: The MQTT client instance.
            userdata: Private user data (unused).
            message: The received MQTTMessage object (message.topic, message.payload).
        """
        topic = str(getattr(message, "topic", ""))
        payload_bytes = getattr(message, "payload", b"")

        try:
            payload_text = payload_bytes.decode("utf-8")
        except Exception:
            logger.warning("Non-utf8 MQTT payload on topic=%s", topic, exc_info=True)
            return

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            logger.debug("Non-JSON MQTT payload on topic=%s: %r", topic, payload_text)
            return

        if not isinstance(payload, dict):
            logger.debug("Ignoring non-object JSON payload on topic=%s: %r", topic, payload)
            return

        device = self._device_from_topic(topic)
        numeric_fields = self._extract_numeric_fields(payload)
        if not numeric_fields:
            return

        parsed = ParsedSensorData(
            device=device,
            topic=topic,
            received_at=datetime.now(timezone.utc),
            fields=numeric_fields,
        )

        if self._on_sensor_data is None:
            logger.debug("Parsed sensor data but no sink configured: %s", parsed)
            return

        try:
            self._on_sensor_data(parsed)
        except Exception:
            logger.exception("Sensor data sink raised; topic=%s device=%s", topic, device)

    @property
    def is_connected(self) -> bool:
        return self._connected

    @staticmethod
    def _device_from_topic(topic: str) -> str:
        """
        For Zigbee2MQTT default topics: zigbee2mqtt/<friendlyName>
        """
        prefix = "zigbee2mqtt/"
        if topic.startswith(prefix) and len(topic) > len(prefix):
            return topic[len(prefix) :]
        return topic

    @staticmethod
    def _extract_numeric_fields(payload: Mapping[str, Any]) -> dict[str, float]:
        fields: dict[str, float] = {}
        for key, value in payload.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                fields[str(key)] = float(value)
        return fields
