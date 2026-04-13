## Plant Tracker Architecture

This document describes the system architecture and runtime data flow for the Plant Tracker, based on `docs/image.png`.

## High-level overview

The system is split into three logical areas:

- **Location: Salón (Raspberry Pi / edge)**: Zigbee sensors publish measurements via MQTT.
- **Location: Despacho (ZimaBoard / core server)**: Mosquitto receives MQTT messages; a Python subscriber processes and persists time-series data in InfluxDB v2; a custom FastAPI backend exposes REST endpoints and (optionally) websockets for clients; dashboards read historical data from InfluxDB.
- **Clients (viewing)**: Glance dashboard and/or a custom app display current status and historical metrics.

## Component diagram

```mermaid
flowchart LR
  %% ========== EDGE (SALÓN) ==========
  subgraph EDGE["Location: Salón (Raspberry Pi / Edge)"]
    direction TB

    SENSORS["Zigbee soil moisture sensors\n(Tuya/Zigbee 3.0)\n+ Zigbee air quality sensor"]
    ZBDONGLE["Sonoff ZBDongle-P\n(Zigbee coordinator)\n(USB extension cable)"]

    subgraph RPI["Raspberry Pi (remote antenna)"]
      direction TB
      Z2M["zigbee2mqtt\n(Docker)"]
    end

    SENSORS -->|Zigbee 3.0 wireless| ZBDONGLE --> Z2M
  end

  %% ========== CORE (ZIMABOARD) ==========
  subgraph CORE["Location: Despacho (ZimaBoard / Core Server)"]
    direction TB

    MOSQ["Mosquitto\n(MQTT broker)\n(Docker)"]
    SUB["Backend subscription\n(Python)\n(MQTT client)"]
    INFLUX["InfluxDB v2\n(Time-series DB)\n(Docker)"]
    API["Custom backend\n(FastAPI/Python)\n(Docker)"]
    GLANCE["Glance\n(Dashboard)\n(Docker)"]

    MOSQ -->|MQTT messages| SUB -->|write time-series data| INFLUX
    API <-->|read historical data| INFLUX
    API -->|REST API endpoints| GLANCE
  end

  %% ========== CLIENTS ==========
  subgraph CLIENTS["Clients (Viewing)"]
    direction TB
    MONITOR["ZimaBoard monitor\n(Glance dashboard)"]
    TABLET["Custom app\n(Tablet)"]
  end

  %% ========== NETWORK / INTEGRATION ==========
  Z2M -->|MQTT publish\nTopic: zigbee2mqtt/<deviceFriendlyName>\nPayload: JSON (e.g. humidity, temperature, etc.)| MOSQ

  GLANCE --> MONITOR
  API -->|REST API| TABLET
  API -.->|WebSockets (MQTT)\n(optional)| TABLET
```

## Data flow

### Sensor → MQTT publish (edge)

- **Zigbee sensors** (soil moisture, air quality, etc.) communicate over **Zigbee 3.0** to the **Sonoff ZBDongle-P** coordinator.
- The **Raspberry Pi** runs **`zigbee2mqtt`** (in Docker), which translates Zigbee device events into **MQTT publishes**.
- Messages are published under topics like:
  - `zigbee2mqtt/<deviceFriendlyName>`
- Payloads are JSON objects containing measurements (example fields shown in the diagram: `humidity`, `temperature`).

### MQTT broker → subscriber → InfluxDB (core)

- The **ZimaBoard** runs **Mosquitto** (MQTT broker) in Docker and receives the MQTT messages.
- A **Python MQTT subscriber** (“backend subscription”) subscribes to relevant topics, parses payloads, and **writes time-series points into InfluxDB v2**.

### InfluxDB → API/dashboards → clients (core + clients)

- The **custom backend** (FastAPI/Python) reads historical data from **InfluxDB v2** and exposes **REST API endpoints** (and optionally websockets) for UI clients.
- **Glance** (running on the ZimaBoard) queries the backend via REST endpoints (e.g., status endpoints) to render the on-device dashboard.
- A **custom app** (tablet) can query the backend over REST, and optionally receive real-time updates over websockets (as depicted).

## Runtime notes

- **Networking**: the Raspberry Pi and ZimaBoard communicate over the **local network (Ethernet/Wi‑Fi)**.
- **Containerization**: core services are shown as Docker containers (Mosquitto, InfluxDB v2, custom backend, Glance). `zigbee2mqtt` runs in Docker on the Raspberry Pi.

## Repository mapping (where to look in this repo)

- **MQTT subscriber / ingestion**: `app/mqtt_client.py`
- **HTTP API / service entrypoint**: `app/main.py`
- **InfluxDB integration**: `app/influx_manager.py`
- **Local stack orchestration**: `docker-compose.yml`
- **MQTT broker configuration**: `config/mosquitto.conf`

