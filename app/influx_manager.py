"""
influx_manager.py — InfluxDB v2 connection and write manager.

Responsibilities:
- Connect to InfluxDB v2 using the official Python client.
- Write sensor data points to the configured bucket.
- (Optional) Query data points for the API layer.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Mapping

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)


class InfluxManager:
    """Manages the connection and write operations for InfluxDB v2."""

    def __init__(
        self,
        url: str = os.getenv("INFLUXDB_URL", "http://influxdb:8086"),
        token: str = os.getenv("INFLUXDB_TOKEN", ""),
        org: str = os.getenv("INFLUXDB_ORG", "plant-tracker"),
        bucket: str = os.getenv("INFLUXDB_BUCKET", "sensors"),
    ):
        """
        Initialise the InfluxDB manager with connection parameters.

        All parameters default to environment variables so that they can be
        injected via Docker Compose without modifying the source code.

        Args:
            url: URL of the InfluxDB v2 instance (e.g. http://influxdb:8086).
            token: Authentication token generated in the InfluxDB UI.
            org: Organisation name configured in InfluxDB.
            bucket: Target bucket where sensor data will be written.
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_sensor_data(
        self, measurement: str, tags: Mapping[str, str], fields: Mapping[str, Any]
    ) -> None:
        """
        Write a single data point to InfluxDB.

        Args:
            measurement: The InfluxDB measurement name (e.g. "zigbee_sensor").
            tags: Dictionary of tag key/value pairs (e.g. {"device_id": "0x1234"}).
            fields: Dictionary of field key/value pairs holding the sensor readings
                    (e.g. {"temperature": 22.5, "humidity": 60.0}).
        """
        point = Point(measurement)
        for key, value in tags.items():
            point = point.tag(str(key), str(value))

        for key, value in fields.items():
            if value is None:
                continue
            # InfluxDB enforces a single type per field name. Earlier versions of this
            # app stored numeric fields as floats, so we normalize ints to floats to
            # avoid "field type conflict" partial writes (e.g. battery: int vs float).
            if isinstance(value, bool):
                point = point.field(str(key), value)
            elif isinstance(value, int):
                point = point.field(str(key), float(value))
            else:
                point = point.field(str(key), value)

        try:
            self.write_api.write(
                bucket=self.bucket,
                org=self.org,
                record=point,
                write_precision=WritePrecision.S,
            )
        except Exception:
            logger.exception(
                "Influx write failed (bucket=%s org=%s measurement=%s)",
                self.bucket,
                self.org,
                measurement,
            )

    def query_sensor_data(self, query: str) -> list:
        """
        Execute a Flux query and return the results as a list of records.

        Args:
            query: A Flux query string targeting self.bucket and self.org.

        Returns:
            A list of FluxRecord objects (empty list if the query returns nothing).
        """
        try:
            query_api = self.client.query_api()
            tables = query_api.query(query=query, org=self.org)
        except Exception:
            logger.exception("Influx query failed (org=%s)", self.org)
            return []

        records: list[Any] = []
        for table in tables:
            records.extend(table.records)
        return records

    def list_devices(self, measurement: str = "zigbee_sensor", lookback: str = "30d") -> list[str]:
        query = f"""
from(bucket: "{self.bucket}")
  |> range(start: -{lookback})
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> filter(fn: (r) => r.device != "bridge" and r.device !~ /^bridge\\//)
  |> keep(columns: ["device"])
  |> distinct(column: "device")
"""
        records = self.query_sensor_data(query)
        devices: set[str] = set()
        for record in records:
            try:
                device = record.values.get("device")
            except Exception:
                device = None
            if isinstance(device, str) and device:
                devices.add(device)
        return sorted(devices)

    def latest_fields(
        self,
        device: str,
        measurement: str = "zigbee_sensor",
        lookback: str = "24h",
    ) -> tuple[datetime | None, dict[str, Any]]:
        query = f"""
from(bucket: "{self.bucket}")
  |> range(start: -{lookback})
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> filter(fn: (r) => r.device == "{device}")
  |> last()
"""
        records = self.query_sensor_data(query)

        fields: dict[str, Any] = {}
        latest_time: datetime | None = None

        for record in records:
            values = getattr(record, "values", None)
            if not isinstance(values, dict):
                continue

            field = values.get("_field")
            value = values.get("_value")
            time = values.get("_time")

            if isinstance(field, str) and value is not None and isinstance(value, (bool, int, float, str)):
                fields[field] = value

            # _time is typically a datetime; accept strings defensively.
            if isinstance(time, datetime):
                if time.tzinfo is None:
                    time = time.replace(tzinfo=timezone.utc)
                latest_time = time if latest_time is None or time > latest_time else latest_time
            elif isinstance(time, str):
                try:
                    parsed = datetime.fromisoformat(time.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    latest_time = parsed if latest_time is None or parsed > latest_time else latest_time
                except Exception:
                    pass

        return latest_time, fields

    def close(self) -> None:
        """
        Close the InfluxDB client connection and release resources.
        """
        try:
            self.client.close()
        except Exception:
            logger.exception("Failed to close InfluxDB client")
