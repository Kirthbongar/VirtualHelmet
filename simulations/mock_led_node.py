import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import json
import time

import yaml

from shared.mqtt_client import MQTTClient
from shared.constants import (
    TOPIC_LEDS_EYES,
    TOPIC_LEDS_ACCENT,
    TOPIC_LEDS_ALERT,
    TOPIC_SYSTEM_HEARTBEAT,
    NODE_LED,
)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'sim_config.yaml')


def load_config():
    with open(_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def on_eyes(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        pattern = data.get("pattern", "?")
        color = data.get("color", "?")
        brightness = data.get("brightness", "?")
        print(f"[LED EYES]   pattern={pattern}  color={color}  brightness={brightness}")
    except Exception as e:
        print(f"[LED EYES]   <parse error: {e}> raw={message.payload}")


def on_accent(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        pattern = data.get("pattern", "?")
        color = data.get("color", "?")
        brightness = data.get("brightness", "?")
        print(f"[LED ACCENT] pattern={pattern}  color={color}  brightness={brightness}")
    except Exception as e:
        print(f"[LED ACCENT] <parse error: {e}> raw={message.payload}")


def on_alert(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        alert_type = data.get("type", "?")
        active = data.get("active", "?")
        print(f"[LED ALERT]  type={alert_type}  active={active}")
    except Exception as e:
        print(f"[LED ALERT]  <parse error: {e}> raw={message.payload}")


async def publish_heartbeat(client: MQTTClient):
    while True:
        payload = {"node": NODE_LED, "timestamp": time.time()}
        client.publish(TOPIC_SYSTEM_HEARTBEAT, json.dumps(payload))
        await asyncio.sleep(30)


async def main():
    cfg = load_config()
    mqtt_cfg = cfg["mqtt"]

    client = MQTTClient(
        broker_host=mqtt_cfg["broker_host"],
        broker_port=mqtt_cfg["broker_port"],
        client_id="sim-led-node",
    )
    client.connect()

    client.subscribe(TOPIC_LEDS_EYES, on_eyes)
    client.subscribe(TOPIC_LEDS_ACCENT, on_accent)
    client.subscribe(TOPIC_LEDS_ALERT, on_alert)

    print(f"[mock_led_node] Connected to {mqtt_cfg['broker_host']}:{mqtt_cfg['broker_port']}")
    print(f"[mock_led_node] Monitoring: {TOPIC_LEDS_EYES}, {TOPIC_LEDS_ACCENT}, {TOPIC_LEDS_ALERT}")

    await publish_heartbeat(client)


if __name__ == "__main__":
    asyncio.run(main())
