import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import time
import logging

from shared.mqtt_client import MQTTClient
from shared.constants import TOPIC_POWER_BATTERY, TOPIC_SYSTEM_HEARTBEAT, NODE_POWER
from shared.config_loader import load_config
from battery import BatteryMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_S = 30


async def main():
    config = load_config(os.path.join(os.path.dirname(__file__), '..', 'config', 'power-node.yaml'))

    broker_host = config['mqtt']['broker_host']
    broker_port = config['mqtt']['broker_port']
    capacity_wh = config['battery']['capacity_wh']
    shunt_ohms = config['battery']['shunt_ohms']
    poll_interval_s = config['battery']['poll_interval_s']

    mqtt = MQTTClient(broker_host, broker_port)
    await mqtt.connect()

    monitor = BatteryMonitor(shunt_ohms=shunt_ohms, capacity_wh=capacity_wh)

    last_heartbeat = 0.0

    while True:
        now = time.time()

        try:
            payload = monitor.read()
            payload['timestamp'] = now
            await mqtt.publish(TOPIC_POWER_BATTERY, payload)
        except Exception as exc:
            logger.error("Battery read/publish error: %s", exc)

        if now - last_heartbeat >= HEARTBEAT_INTERVAL_S:
            try:
                await mqtt.publish(TOPIC_SYSTEM_HEARTBEAT, {
                    'node': NODE_POWER,
                    'timestamp': now,
                })
                last_heartbeat = now
            except Exception as exc:
                logger.error("Heartbeat publish error: %s", exc)

        await asyncio.sleep(poll_interval_s)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Power node shutting down.")
