# Setup Guide

End-to-end instructions for running Plant Tracker across two machines:

- **ZimaBoard** — Mosquitto (MQTT broker), InfluxDB v2, Plant Tracker API
- **Raspberry Pi** — Zigbee2MQTT + Sonoff ZBDongle-P USB coordinator

---

## 1. ZimaBoard

### 1.1 Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:


| Variable                 | What to set                                          |
| ------------------------ | ---------------------------------------------------- |
| `INFLUXDB_ADMIN_TOKEN`   | A strong random string (e.g. `openssl rand -hex 32`) |
| `INFLUXDB_INIT_PASSWORD` | A strong password for the InfluxDB admin user        |
| `INFLUXDB_TOKEN`         | Same value as `INFLUXDB_ADMIN_TOKEN`                 |


The other defaults (`plant-tracker` org, `sensors` bucket, port `8086`) are fine as-is.

### 1.2 Start services

```bash
docker compose up -d
```

This starts:

- **Mosquitto** on port `1883` (MQTT broker — accessible from the Pi)
- **InfluxDB** on port `8086` (UI at `http://ZIMABOARD_IP:8086`)
- **Plant Tracker API** on port `8000`

### 1.3 Verify

```bash
# Check all containers are healthy
docker compose ps

# Test the API
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok", "mqtt_connected": true, "influx_configured": true, ...}
```

> **Note on firewall:** Mosquitto binds to `0.0.0.0:1883` and Docker maps the port to the host, so the Pi can reach it over your LAN. If you have `ufw` or `iptables` rules, allow port `1883` from your local network.

---

## 2. Raspberry Pi (fresh Raspberry Pi OS)

### 2.1 Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Log out and back in (or reboot) for the group change to take effect.

### 2.2 Plug in the ZBDongle-P and find its device path

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

The Sonoff ZBDongle-P usually appears as `/dev/ttyACM0`. If it's different, update the `devices:` section in `docker-compose.pi.yml` and the `serial.port` in `config/zigbee2mqtt/configuration.yaml`.

### 2.3 Copy project files to the Pi

Run this from your Mac (replace `PIIP` with the Pi's LAN IP):

```bash
scp docker-compose.pi.yml pi@PIIP:~/plant-tracker/
scp -r config/zigbee2mqtt pi@PIIP:~/plant-tracker/config/
```

Or clone/pull the repo directly on the Pi:

```bash
git clone <repo-url> ~/plant-tracker
```

### 2.4 Set the ZimaBoard IP

On the Pi, edit `~/plant-tracker/config/zigbee2mqtt/configuration.yaml` and replace `ZIMABOARD_IP` with your ZimaBoard's actual LAN IP:

```bash
nano ~/plant-tracker/config/zigbee2mqtt/configuration.yaml
# Change: server: mqtt://ZIMABOARD_IP:1883
# To:     server: mqtt://192.168.1.X:1883
```

### 2.5 Start Zigbee2MQTT

```bash
cd ~/plant-tracker
docker compose -f docker-compose.pi.yml up -d
```

Watch the logs to confirm it connected:

```bash
docker logs -f zigbee2mqtt
```

Look for a line like:

```
Zigbee2MQTT:info  Connected to MQTT server
```

The Zigbee2MQTT web UI is available at `http://PIIP:8080`.

---

## 3. Pairing Soil Moisture Sensors

With `permit_join: true` set in the config (the default), the coordinator is ready to accept new devices.

1. Trigger pairing mode on a sensor:
  - Most Zigbee soil sensors: hold the reset/pair button for 5 seconds, or remove and reinsert the battery.
  - The sensor LED usually flashes rapidly when in pairing mode.
2. Watch the logs on the Pi:
  ```bash
   docker logs -f zigbee2mqtt
  ```
   You should see a message like:
3. Repeat for each sensor.
4. **Optional — rename sensors** for readable API output. Edit `config/zigbee2mqtt/configuration.yaml` on the Pi and add a `devices:` block:
  ```yaml
   devices:
     '0x00158d0001234567':
       friendly_name: plant_livingroom
     '0x00158d0007654321':
       friendly_name: plant_bedroom
  ```
   Then restart:
5. **Disable join mode** once all sensors are paired:
  ```yaml
   permit_join: false
  ```
   Restart Zigbee2MQTT again.

---

## 4. Verify End-to-End

Use `requests.http` in the project root (works with the Cursor / VS Code REST Client), or `curl`:

```bash
# List paired sensors
curl http://ZIMABOARD_IP:8000/devices

# Latest reading for all sensors
curl http://ZIMABOARD_IP:8000/devices/latest

# Latest reading for one sensor
curl http://ZIMABOARD_IP:8000/devices/plant_livingroom/latest
```

You can also browse the raw data in InfluxDB at `http://ZIMABOARD_IP:8086` → Data Explorer → `sensors` bucket → `zigbee_sensor` measurement.

---

## 5. Glance dashboard

If you use the Glance self-hosted dashboard, you can display the latest sensor readings directly from the API using a `custom-api` widget.

See [`docs/GLANCE.md`](GLANCE.md).

---

## Troubleshooting


| Symptom                                      | Check                                                                             |
| -------------------------------------------- | --------------------------------------------------------------------------------- |
| `mqtt_connected: false` in `/health`         | MQTT broker is not running, or firewall blocks port 1883                          |
| No devices in `/devices`                     | Sensors haven't sent data in the last 30 days, or Zigbee2MQTT isn't connected     |
| `zigbee2mqtt` log: "Cannot open serial port" | Wrong device path — check `ls /dev/ttyACM* /dev/ttyUSB*` on the Pi                |
| Sensor doesn't pair                          | Hold pairing button longer; ensure `permit_join: true` and Zigbee2MQTT is running |


