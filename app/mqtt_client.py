"""
mqtt_client.py — MQTT client for receiving Zigbee sensor data.

Responsibilities:
- Connect to the Mosquitto broker.
- Subscribe to the configured topic(s).
- Parse incoming messages and forward them to the InfluxDB manager.
"""

import os
# TODO: Install and import the paho-mqtt library: pip install paho-mqtt
# import paho.mqtt.client as mqtt


class MQTTClient:
    """Manages the connection to the MQTT broker and message handling."""

    def __init__(
        self,
        broker_host: str = os.getenv("MQTT_BROKER_HOST", "mosquitto"),
        broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883")),
        topic: str = os.getenv("MQTT_TOPIC", "zigbee2mqtt/#"),
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
        # TODO: Create the paho mqtt.Client instance.
        # self.client = mqtt.Client()

    def connect(self) -> None:
        """
        Establish a connection to the MQTT broker and start the network loop.

        TODO: Call self.client.connect(self.broker_host, self.broker_port).
        TODO: Register on_connect and on_message callbacks.
        TODO: Call self.client.loop_start() to run the loop in a background thread.
        """
        pass

    def disconnect(self) -> None:
        """
        Stop the network loop and disconnect from the broker cleanly.

        TODO: Call self.client.loop_stop().
        TODO: Call self.client.disconnect().
        """
        pass

    def _on_connect(self, client, userdata, flags, rc: int) -> None:
        """
        Callback executed when the client connects to the broker.

        Args:
            client: The MQTT client instance.
            userdata: Private user data (unused).
            flags: Response flags from the broker.
            rc: Connection result code (0 = success).

        TODO: Log the connection result.
        TODO: If rc == 0, subscribe to self.topic via client.subscribe(self.topic).
        TODO: Handle connection errors for non-zero rc values.
        """
        pass

    def _on_message(self, client, userdata, message) -> None:
        """
        Callback executed for every message received on a subscribed topic.

        Args:
            client: The MQTT client instance.
            userdata: Private user data (unused).
            message: The received MQTTMessage object (message.topic, message.payload).

        TODO: Decode message.payload (JSON expected from Zigbee2MQTT).
        TODO: Extract sensor readings (temperature, humidity, etc.).
        TODO: Forward the parsed data to the InfluxManager for storage.
        """
        pass
