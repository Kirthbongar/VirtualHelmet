import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import json
import time

import yaml

from shared.mqtt_client import MQTTClient
from shared.constants import TOPIC_POWER_BATTERY, TOPIC_SYSTEM_HEARTBEAT, NODE_POWER

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'sim_config.yaml')

# Voltage lookup table: (soc_pct, voltage)
_SOC_VOLTAGE_TABLE = [
    (100, 8.4),
    (90,  8.2),
    (80,  8.0),
    (70,  7.8),
    (60,  7.6),
    (50,  7.4),
    (40,  7.2),
    (30,  7.0),
    (20,  6.8),
    (10,  6.5),
    (0,   6.0),
]


def soc_to_voltage(soc: float) -> float:
    soc = max(0.0, min(100.0, soc))
    for i in range(len(_SOC_VOLTAGE_TABLE) - 1):
        high_soc, high_v = _SOC_VOLTAGE_TABLE[i]
        low_soc, low_v = _SOC_VOLTAGE_TABLE[i + 1]
        if soc >= low_soc:
            ratio = (soc - low_soc) / (high_soc - low_soc)
            return round(low_v + ratio * (high_v - low_v), 3)
    return _SOC_VOLTAGE_TABLE[-1][1]


def load_config():
    with open(_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


async def publish_battery(client: MQTTClient, drain_rate_pct_per_min: float, poll_interval_s: float):
    soc = 85.0
    capacity_wh = 37.0
    current_ma = 1200.0
    last_time = time.time()

    while True:
        now = time.time()
        elapsed_min = (now - last_time) / 60.0
        last_time = now

        soc = max(0.0, soc - drain_rate_pct_per_min * elapsed_min)
        voltage = soc_to_voltage(soc)
        power_w = voltage * current_ma / 1000.0
        remaining_wh = capacity_wh * (soc / 100.0)
        eta_min = (remaining_wh / power_w * 60.0) if power_w > 0 else 0.0

        payload = {
            "soc_pct": round(soc, 2),
            "voltage": voltage,
            "current_ma": current_ma,
            "power_w": round(power_w, 3),
            "charging": False,
            "eta_min": round(eta_min, 1),
            "capacity_wh": capacity_wh,
            "remaining_wh": round(remaining_wh, 3),
            "timestamp": now,
        }
        client.publish(TOPIC_POWER_BATTERY, json.dumps(payload))
        await asyncio.sleep(poll_interval_s)


async def publish_heartbeat(client: MQTTClient):
    while True:
        payload = {"node": NODE_POWER, "timestamp": time.time()}
        client.publish(TOPIC_SYSTEM_HEARTBEAT, json.dumps(payload))
        await asyncio.sleep(30)


async def main():
    cfg = load_config()
    mqtt_cfg = cfg["mqtt"]
    sim_cfg = cfg["simulation"]

    client = MQTTClient(
        broker_host=mqtt_cfg["broker_host"],
        broker_port=mqtt_cfg["broker_port"],
        client_id="sim-power-node",
    )
    client.connect()

    print(f"[mock_power_node] Connected to {mqtt_cfg['broker_host']}:{mqtt_cfg['broker_port']}")

    await asyncio.gather(
        publish_battery(
            client,
            sim_cfg["battery_drain_rate_pct_per_min"],
            sim_cfg["power_poll_interval_s"],
        ),
        publish_heartbeat(client),
    )


if __name__ == "__main__":
    asyncio.run(main())
