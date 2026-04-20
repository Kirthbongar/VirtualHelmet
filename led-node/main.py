import sys
import os
import json
import asyncio
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from mqtt_client import MQTTClient
from constants import (
    TOPIC_LEDS_EYES,
    TOPIC_LEDS_ACCENT,
    TOPIC_LEDS_ALERT,
    TOPIC_SYSTEM_HEARTBEAT,
    NODE_LED,
)
from config_loader import load_config
from led_node.controller import LEDController

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'led-node.yaml')


def build_controller(cfg):
    leds = cfg['leds']
    eyes_cfg = {
        'gpio_pin': leds['eyes']['gpio_pin'],
        'led_count': leds['eyes']['led_count'],
        'default_color': tuple(leds['eyes']['default_color']),
        'default_brightness': leds['eyes']['default_brightness'],
    }
    accent_cfg = {
        'gpio_pin': leds['accent']['gpio_pin'],
        'led_count': leds['accent']['led_count'],
        'default_color': tuple(leds['accent']['default_color']),
        'default_brightness': leds['accent']['default_brightness'],
    }
    return LEDController(eyes_cfg, accent_cfg, leds['max_brightness'])


def make_eyes_handler(controller):
    def handle(topic, payload):
        try:
            color = tuple(payload['color'])
            brightness = int(payload['brightness'])
            pattern = str(payload['pattern'])
            controller.set_color_pattern('eyes', color, brightness, pattern)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Bad eyes payload: %s — %s", payload, e)
    return handle


def make_accent_handler(controller):
    def handle(topic, payload):
        try:
            color = tuple(payload['color'])
            brightness = int(payload['brightness'])
            pattern = str(payload['pattern'])
            controller.set_color_pattern('accent', color, brightness, pattern)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Bad accent payload: %s — %s", payload, e)
    return handle


def make_alert_handler(controller):
    def handle(topic, payload):
        try:
            alert_type = str(payload['type'])
            active = bool(payload['active'])
            controller.set_alert(alert_type, active)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Bad alert payload: %s — %s", payload, e)
    return handle


async def heartbeat_loop(mqtt_client):
    while True:
        await asyncio.sleep(30)
        mqtt_client.publish(TOPIC_SYSTEM_HEARTBEAT, {'node': NODE_LED, 'ts': time.time()})


async def main():
    cfg = load_config(CONFIG_PATH)

    controller = build_controller(cfg)

    mqtt_cfg = cfg['mqtt']
    mqtt_client = MQTTClient(
        broker_host=mqtt_cfg['broker_host'],
        broker_port=mqtt_cfg['broker_port'],
        client_id=NODE_LED,
    )

    mqtt_client.subscribe(TOPIC_LEDS_EYES, make_eyes_handler(controller))
    mqtt_client.subscribe(TOPIC_LEDS_ACCENT, make_accent_handler(controller))
    mqtt_client.subscribe(TOPIC_LEDS_ALERT, make_alert_handler(controller))

    mqtt_client.connect()
    logger.info("LED node started")

    try:
        await heartbeat_loop(mqtt_client)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down LED node")
    finally:
        controller.clear()
        mqtt_client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
