"""Sensor node entry point — reads IMU, compass, environment, and air quality sensors."""

import asyncio
import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.mqtt_client import MQTTClient
from shared.constants import (
    TOPIC_SENSORS_IMU,
    TOPIC_SENSORS_ENVIRONMENT,
    TOPIC_SENSORS_AIRQUALITY,
    TOPIC_SYSTEM_HEARTBEAT,
    NODE_SENSOR,
)
from shared.config_loader import load_config

from sensors.imu import run_imu_task
from sensors.compass import Compass
from sensors.environment import run_environment_task
from sensors.airquality import run_airquality_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'sensor-node.yaml')


async def heartbeat_task(mqtt_client: MQTTClient, interval_s: float = 10.0) -> None:
    while True:
        try:
            mqtt_client.publish(TOPIC_SYSTEM_HEARTBEAT, {
                "node": NODE_SENSOR,
                "timestamp": time.time(),
            })
        except Exception as exc:
            logger.warning("Heartbeat publish failed: %s", exc)
        await asyncio.sleep(interval_s)


async def main() -> None:
    config = load_config(CONFIG_PATH)

    broker_host = config["mqtt"]["broker_host"]
    broker_port = config["mqtt"]["broker_port"]

    mqtt_client = MQTTClient(
        broker_host=broker_host,
        broker_port=broker_port,
        client_id=f"{NODE_SENSOR}-node",
    )
    mqtt_client.connect()

    sensors_cfg = config.get("sensors", {})
    imu_cfg = sensors_cfg.get("imu", {})
    compass_cfg = sensors_cfg.get("compass", {})
    env_cfg = sensors_cfg.get("environment", {})
    aq_cfg = sensors_cfg.get("airquality", {})

    compass = Compass(
        declination_deg=float(compass_cfg.get("declination_deg", 0.0)),
    )

    try:
        await asyncio.gather(
            run_imu_task(mqtt_client, imu_cfg, compass),
            run_environment_task(mqtt_client, env_cfg),
            run_airquality_task(mqtt_client, aq_cfg),
            heartbeat_task(mqtt_client),
        )
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sensor node stopped by user")
    finally:
        logger.info("Sensor node shut down cleanly")
