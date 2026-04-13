"""
influx_manager.py — InfluxDB v2 connection and write manager.

Responsibilities:
- Connect to InfluxDB v2 using the official Python client.
- Write sensor data points to the configured bucket.
- (Optional) Query data points for the API layer.
"""

import os
# TODO: Install and import the InfluxDB v2 client: pip install influxdb-client
# from influxdb_client import InfluxDBClient, Point, WritePrecision
# from influxdb_client.client.write_api import SYNCHRONOUS


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
        # TODO: Create the InfluxDBClient instance.
        # self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        # TODO: Create the write API.
        # self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_sensor_data(self, measurement: str, tags: dict, fields: dict) -> None:
        """
        Write a single data point to InfluxDB.

        Args:
            measurement: The InfluxDB measurement name (e.g. "zigbee_sensor").
            tags: Dictionary of tag key/value pairs (e.g. {"device_id": "0x1234"}).
            fields: Dictionary of field key/value pairs holding the sensor readings
                    (e.g. {"temperature": 22.5, "humidity": 60.0}).

        TODO: Build a Point object from measurement, tags, and fields.
        TODO: Call self.write_api.write(bucket=self.bucket, org=self.org, record=point).
        TODO: Handle and log any write errors.
        """
        pass

    def query_sensor_data(self, query: str) -> list:
        """
        Execute a Flux query and return the results as a list of records.

        Args:
            query: A Flux query string targeting self.bucket and self.org.

        Returns:
            A list of FluxRecord objects (empty list if the query returns nothing).

        TODO: Create a query API via self.client.query_api().
        TODO: Execute the query and return the result tables/records.
        TODO: Handle and log any query errors.
        """
        # TODO: Implement query logic.
        return []

    def close(self) -> None:
        """
        Close the InfluxDB client connection and release resources.

        TODO: Call self.client.close().
        """
        pass
