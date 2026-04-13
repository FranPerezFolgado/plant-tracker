## Dashboard API

This document describes the REST endpoints used by dashboards (Glance and custom clients) to read sensor data stored in InfluxDB.

### Flow

```mermaid
flowchart TD
  dashboard[DashboardClient] -->|GET /devices| api[FastAPI]
  dashboard -->|GET /devices/latest| api
  dashboard -->|GET /devices/{device}/latest| api
  api --> influxMgr[InfluxManager]
  influxMgr --> influxdb[InfluxDBv2]
```

### Endpoints

#### `GET /devices`

Returns known devices (derived from the `device` tag in Influx).

Response:

```json
{ "devices": ["living_room", "plant_1"] }
```

#### `GET /devices/latest`

Returns latest values for all devices in one call (best for Glance).

Response:

```json
{
  "devices": [
    { "device": "living_room", "time": "2026-01-01T00:00:00+00:00", "fields": { "temperature": 21.5 } },
    { "device": "plant_1", "time": null, "fields": {} }
  ]
}
```

#### `GET /devices/{device}/latest`

Returns latest values for a single device.

Response:

```json
{ "device": "living_room", "time": "2026-01-01T00:00:00+00:00", "fields": { "temperature": 21.5, "humidity": 60 } }
```

### Notes

- **Measurement**: `zigbee_sensor`
- **Tags**: at minimum `device` (and `topic` is written as well)
- **Fields**: numeric keys extracted from Zigbee2MQTT JSON payloads

