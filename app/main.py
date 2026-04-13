"""
main.py — Entry point for the Plant Tracker FastAPI application.

Responsibilities:
- Initialise the FastAPI app.
- Register routers / endpoints.
- Start background services (MQTT client, InfluxDB connection) on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifecycle using the recommended lifespan context manager.

    Code before the ``yield`` runs on startup; code after runs on shutdown.

    TODO: Initialise the MQTTClient and start listening for messages.
    TODO: Initialise the InfluxManager and verify the connection.
    """
    # ── Startup ───────────────────────────────────────────────────────────
    # TODO: Create and connect the MQTTClient instance here.
    # TODO: Create and verify the InfluxManager connection here.

    yield  # Application is running

    # ── Shutdown ──────────────────────────────────────────────────────────
    # TODO: Gracefully disconnect the MQTTClient.
    # TODO: Close the InfluxDB client connection.


app = FastAPI(
    title="Plant Tracker API",
    description="Exposes Zigbee sensor data collected via MQTT and stored in InfluxDB.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health-check endpoint.

    Returns a simple JSON payload indicating that the service is running.
    Extend this endpoint to also report the status of MQTT and InfluxDB
    connections when the logic is implemented.
    """
    # TODO: Add MQTT and InfluxDB connectivity status to the response.
    return {"status": "ok"}
