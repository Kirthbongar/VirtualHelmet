import sys
import os
import asyncio
import logging
import time
import serial

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.mqtt_client import MQTTClient
from shared.constants import TOPIC_LIDAR_DISTANCE, TOPIC_SYSTEM_HEARTBEAT, NODE_BRAIN
from shared.config_loader import load_config
from brain.lidar.tfmini import TFminiS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'brain.yaml')


async def run():
    cfg = load_config(CONFIG_PATH)
    lidar_cfg = cfg.get('lidar', {})

    port         = lidar_cfg.get('port', '/dev/ttyAMA0')
    baudrate     = lidar_cfg.get('baud', 115200)
    poll_hz      = lidar_cfg.get('poll_hz', 10)
    min_strength = lidar_cfg.get('min_strength', 100)

    mqtt_cfg = cfg.get('mqtt', {})
    mqtt = MQTTClient(
        broker=mqtt_cfg.get('broker_host', 'localhost'),
        port=mqtt_cfg.get('broker_port', 1883),
        client_id="brain-lidar",
    )
    mqtt.connect()

    interval = 1.0 / poll_hz
    lidar = TFminiS(port=port, baudrate=baudrate, min_strength=min_strength)

    last_heartbeat = 0.0

    def open_lidar():
        lidar.open()
        logger.info(f"TFminiS opened on {port} at {baudrate} baud")

    open_lidar()

    try:
        while True:
            loop_start = time.monotonic()

            try:
                frame = lidar.read_frame()
                payload = {
                    "distance_m":  frame["distance_m"],
                    "distance_ft": frame["distance_ft"],
                    "strength":    frame["strength"],
                    "valid":       frame["valid"],
                    "timestamp":   time.time(),
                }
                mqtt.publish(TOPIC_LIDAR_DISTANCE, payload)
            except (IOError, TimeoutError, serial.SerialException) as exc:
                logger.warning(f"LiDAR serial error: {exc} — retrying in 5s")
                try:
                    lidar.close()
                except Exception:
                    pass
                await asyncio.sleep(5)
                try:
                    open_lidar()
                except Exception as reopen_exc:
                    logger.warning(f"LiDAR reopen failed: {reopen_exc}")
                continue

            now = time.time()
            if now - last_heartbeat >= 30:
                mqtt.publish(TOPIC_SYSTEM_HEARTBEAT, {
                    "node":      "brain/lidar",
                    "timestamp": now,
                })
                last_heartbeat = now

            elapsed = time.monotonic() - loop_start
            sleep_for = interval - elapsed
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)

    finally:
        lidar.close()
        mqtt.disconnect()


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("brain/lidar stopped")


if __name__ == "__main__":
    main()
