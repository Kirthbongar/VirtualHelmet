import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import json
import math
import random
import time

import yaml

from shared.mqtt_client import MQTTClient
from shared.constants import (
    TOPIC_GPS_POSITION,
    TOPIC_LIDAR_DISTANCE,
    TOPIC_SYSTEM_HEARTBEAT,
    NODE_BRAIN,
)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'sim_config.yaml')


def load_config():
    with open(_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


async def publish_gps(client: MQTTClient, start_lat: float, start_lon: float, poll_interval_s: float):
    start_time = time.time()
    lat = start_lat
    lon = start_lon

    while True:
        elapsed = time.time() - start_time
        fix_quality = 1 if elapsed >= 5.0 else 0

        # ~0.000001 deg per second in a slowly-rotating direction
        angle = elapsed * 0.1
        lat += math.cos(angle) * 0.000001
        lon += math.sin(angle) * 0.000001

        payload = {
            "lat": round(lat, 8),
            "lon": round(lon, 8),
            "fix_quality": fix_quality,
            "satellites": 8 if fix_quality else 0,
            "altitude_m": 0.0,
            "speed_knots": 0.0,
            "timestamp": time.time(),
        }
        client.publish(TOPIC_GPS_POSITION, json.dumps(payload))
        await asyncio.sleep(poll_interval_s)


async def publish_lidar(client: MQTTClient, poll_hz: float):
    interval = 1.0 / poll_hz
    start = time.time()

    while True:
        elapsed = time.time() - start
        # Oscillates between 0.5m and 5.0m over 10 seconds
        distance = 0.5 + 2.25 * (1.0 + math.sin(2 * math.pi * elapsed / 10.0))

        payload = {
            "distance_m": round(distance, 3),
            "strength": 500,
            "valid": True,
            "timestamp": time.time(),
        }
        client.publish(TOPIC_LIDAR_DISTANCE, json.dumps(payload))
        await asyncio.sleep(interval)


async def publish_heartbeat(client: MQTTClient):
    while True:
        payload = {"node": "brain/gps", "timestamp": time.time()}
        client.publish(TOPIC_SYSTEM_HEARTBEAT, json.dumps(payload))
        await asyncio.sleep(30)


async def main():
    cfg = load_config()
    mqtt_cfg = cfg["mqtt"]
    sim_cfg = cfg["simulation"]

    client = MQTTClient(
        broker_host=mqtt_cfg["broker_host"],
        broker_port=mqtt_cfg["broker_port"],
        client_id="sim-gps-lidar",
    )
    client.connect()

    print(f"[mock_gps_lidar] Connected to {mqtt_cfg['broker_host']}:{mqtt_cfg['broker_port']}")

    await asyncio.gather(
        publish_gps(
            client,
            sim_cfg["gps_start_lat"],
            sim_cfg["gps_start_lon"],
            sim_cfg["gps_poll_interval_s"],
        ),
        publish_lidar(client, sim_cfg["lidar_poll_hz"]),
        publish_heartbeat(client),
    )


if __name__ == "__main__":
    asyncio.run(main())
