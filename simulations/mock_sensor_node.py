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
    TOPIC_SENSORS_IMU,
    TOPIC_SENSORS_ENVIRONMENT,
    TOPIC_SENSORS_AIRQUALITY,
    TOPIC_SYSTEM_HEARTBEAT,
    NODE_SENSOR,
)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'sim_config.yaml')


def load_config():
    with open(_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


async def publish_imu(client: MQTTClient, poll_hz: float):
    interval = 1.0 / poll_hz
    start = time.time()
    heading = 0.0
    while True:
        elapsed = time.time() - start
        pitch = 5.0 * math.sin(2 * math.pi * elapsed / 8.0)
        roll = 5.0 * math.sin(2 * math.pi * elapsed / 11.0 + 1.0)
        heading = (elapsed / 60.0 * 360.0) % 360.0
        yaw = heading + random.uniform(-0.5, 0.5)

        payload = {
            "pitch": round(pitch + random.uniform(-0.1, 0.1), 3),
            "roll": round(roll + random.uniform(-0.1, 0.1), 3),
            "yaw": round(yaw, 3),
            "heading": round(heading, 2),
            "timestamp": time.time(),
        }
        client.publish(TOPIC_SENSORS_IMU, json.dumps(payload))
        await asyncio.sleep(interval)


async def publish_environment(client: MQTTClient):
    while True:
        temp_c = round(22.0 + random.uniform(-0.2, 0.2), 2)
        temp_f = round(temp_c * 9.0 / 5.0 + 32.0, 2)
        payload = {
            "temperature_c": temp_c,
            "temperature_f": temp_f,
            "humidity": round(55.0 + random.uniform(-1.0, 1.0), 2),
            "pressure": 1013.25,
            "timestamp": time.time(),
        }
        client.publish(TOPIC_SENSORS_ENVIRONMENT, json.dumps(payload))
        await asyncio.sleep(5)


async def publish_airquality(client: MQTTClient):
    start = time.time()
    while True:
        elapsed = time.time() - start
        warming_up = elapsed < 20.0
        if warming_up:
            payload = {"warming_up": True, "timestamp": time.time()}
        else:
            payload = {
                "warming_up": False,
                "co2_ppm": round(800.0 + random.uniform(-50.0, 50.0), 1),
                "tvoc_ppb": round(100.0 + random.uniform(-20.0, 20.0), 1),
                "timestamp": time.time(),
            }
        client.publish(TOPIC_SENSORS_AIRQUALITY, json.dumps(payload))
        await asyncio.sleep(10)


async def publish_heartbeat(client: MQTTClient):
    while True:
        payload = {"node": NODE_SENSOR, "timestamp": time.time()}
        client.publish(TOPIC_SYSTEM_HEARTBEAT, json.dumps(payload))
        await asyncio.sleep(30)


async def main():
    cfg = load_config()
    mqtt_cfg = cfg["mqtt"]
    sim_cfg = cfg["simulation"]

    client = MQTTClient(
        broker_host=mqtt_cfg["broker_host"],
        broker_port=mqtt_cfg["broker_port"],
        client_id="sim-sensor-node",
    )
    client.connect()

    print(f"[mock_sensor_node] Connected to {mqtt_cfg['broker_host']}:{mqtt_cfg['broker_port']}")

    await asyncio.gather(
        publish_imu(client, sim_cfg["sensor_poll_hz"]),
        publish_environment(client),
        publish_airquality(client),
        publish_heartbeat(client),
    )


if __name__ == "__main__":
    asyncio.run(main())
