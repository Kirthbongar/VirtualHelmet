import sys
import os
import json
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.mqtt_client import MQTTClient
from shared.constants import (
    TOPIC_SENSORS_IMU, TOPIC_SENSORS_ENVIRONMENT, TOPIC_SENSORS_AIRQUALITY,
    TOPIC_POWER_BATTERY, TOPIC_GPS_POSITION, TOPIC_LIDAR_DISTANCE,
    TOPIC_SYSTEM_HEARTBEAT, TOPIC_HUD_OVERLAY,
)
from shared.config_loader import load_config
from brain.hud.data_store import DataStore
from brain.hud.renderer import HUDRenderer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DATA_TOPICS = [
    TOPIC_SENSORS_IMU,
    TOPIC_SENSORS_ENVIRONMENT,
    TOPIC_SENSORS_AIRQUALITY,
    TOPIC_POWER_BATTERY,
    TOPIC_GPS_POSITION,
    TOPIC_LIDAR_DISTANCE,
    TOPIC_SYSTEM_HEARTBEAT,
]

def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'brain.yaml')
    config = load_config(os.path.abspath(config_path))

    mqtt_cfg = config.get('mqtt', {})
    broker_host = mqtt_cfg.get('broker_host', '192.168.10.1')
    broker_port = mqtt_cfg.get('broker_port', 1883)

    store = DataStore()
    mqtt = MQTTClient(broker_host, broker_port, 'vh-hud')

    renderer = HUDRenderer(store, config)

    def on_data(topic, payload):
        store.update(topic, payload)

    def on_overlay(topic, payload):
        renderer.handle_overlay(payload)

    mqtt.connect()
    for topic in DATA_TOPICS:
        mqtt.subscribe(topic, on_data)
    mqtt.subscribe(TOPIC_HUD_OVERLAY, on_overlay)

    logger.info("HUD service started")
    try:
        renderer.run()  # blocks on main thread — pygame requirement
    except KeyboardInterrupt:
        pass
    finally:
        mqtt.disconnect()
        logger.info("HUD service stopped")

if __name__ == '__main__':
    main()
