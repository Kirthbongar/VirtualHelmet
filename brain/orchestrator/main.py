import sys
import os
import json
import asyncio
import logging
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.mqtt_client import MQTTClient
from shared.constants import (
    TOPIC_VOICE_COMMANDS, TOPIC_SYSTEM_HEARTBEAT, TOPIC_SYSTEM_STATUS,
    TOPIC_SYSTEM_MODE, TOPIC_POWER_BATTERY, TOPIC_SENSORS_AIRQUALITY,
    TOPIC_SENSORS_ENVIRONMENT, TOPIC_SENSORS_IMU, TOPIC_GPS_POSITION,
    TOPIC_LIDAR_DISTANCE, TOPIC_AUDIO_STATUS,
    MODE_BOOT, MODE_ACTIVE, MODE_IDLE, MODE_POWER_SAVE, MODE_ALERT,
    NODE_LED, NODE_SENSOR, NODE_POWER,
)
from shared.config_loader import load_config
from brain.hud.data_store import DataStore
from brain.orchestrator.state_machine import StateMachine
from brain.orchestrator.node_monitor import NodeMonitor
from brain.orchestrator.alert_manager import AlertManager
from brain.orchestrator.command_router import CommandRouter

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Battery alert thresholds (%)
BAT_WARN = 20
BAT_CRIT = 10
BAT_SHUT = 5
# CO2 thresholds (ppm)
CO2_WARN = 1500
CO2_CRIT = 2500
# Temp threshold (°C)
TEMP_WARN = 40.0

def _get_speak():
    try:
        import brain.audio.main as audio_main
        return audio_main.speak
    except Exception:
        return lambda text: logger.info(f"TTS (no audio): {text}")

async def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'brain.yaml')
    config = load_config(os.path.abspath(config_path))

    mqtt_cfg = config.get('mqtt', {})
    broker_host = mqtt_cfg.get('broker_host', '192.168.10.1')
    broker_port = mqtt_cfg.get('broker_port', 1883)

    orch_cfg = config.get('orchestrator', {})
    boot_timeout_s = orch_cfg.get('boot_timeout_s', 30)
    node_offline_threshold_s = orch_cfg.get('node_offline_threshold_s', 120)
    startup_tts = orch_cfg.get('startup_tts', True)
    alert_repeat_interval_s = orch_cfg.get('alert_repeat_interval_s', 60)

    speak = _get_speak()
    store = DataStore()
    mqtt = MQTTClient(broker_host, broker_port, 'vh-orchestrator')
    mqtt.connect()

    sm = StateMachine(mqtt, initial_mode=MODE_BOOT)
    node_mon = NodeMonitor()
    alert_mgr = AlertManager(mqtt, speak, repeat_interval_s=alert_repeat_interval_s)
    router = CommandRouter(mqtt, store, sm, speak)

    # --- Subscribe to all input topics ---
    def on_data(topic, payload):
        store.update(topic, payload)

    def on_heartbeat(topic, payload):
        node_name = payload.get('node', '')
        store.update(topic, payload)
        node_mon.record_heartbeat(node_name, payload.get('timestamp', time.time()))

    def on_voice(topic, payload):
        command = payload.get('command')
        if command:
            router.route(command)

    def on_battery(topic, payload):
        store.update(topic, payload)
        soc = payload.get('soc_percent', 100)
        if soc <= BAT_SHUT:
            alert_mgr.trigger('shutdown_battery')
        elif soc <= BAT_CRIT:
            alert_mgr.trigger('critical_battery')
            alert_mgr.clear('low_battery')
        elif soc <= BAT_WARN:
            alert_mgr.trigger('low_battery')
        else:
            alert_mgr.clear('low_battery')
            alert_mgr.clear('critical_battery')

    def on_airquality(topic, payload):
        store.update(topic, payload)
        if payload.get('warming_up', True):
            return
        co2 = payload.get('co2_ppm', 0)
        if co2 > CO2_CRIT:
            alert_mgr.trigger('co2_critical')
        elif co2 > CO2_WARN:
            alert_mgr.trigger('co2_warning')
            alert_mgr.clear('co2_critical')
        else:
            alert_mgr.clear('co2_warning')
            alert_mgr.clear('co2_critical')

    data_topics = [
        TOPIC_SENSORS_IMU, TOPIC_SENSORS_ENVIRONMENT,
        TOPIC_GPS_POSITION, TOPIC_LIDAR_DISTANCE, TOPIC_AUDIO_STATUS,
    ]
    for t in data_topics:
        mqtt.subscribe(t, on_data)

    mqtt.subscribe(TOPIC_SYSTEM_HEARTBEAT, on_heartbeat)
    mqtt.subscribe(TOPIC_VOICE_COMMANDS, on_voice)
    mqtt.subscribe(TOPIC_POWER_BATTERY, on_battery)
    mqtt.subscribe(TOPIC_SENSORS_AIRQUALITY, on_airquality)

    # --- Boot: wait for nodes ---
    logger.info(f"Boot: waiting up to {boot_timeout_s}s for nodes...")
    boot_start = time.time()
    while time.time() - boot_start < boot_timeout_s:
        statuses = node_mon.check_all(threshold_s=node_offline_threshold_s)
        if all(s == 'online' for s in statuses.values()):
            break
        await asyncio.sleep(2)

    statuses = node_mon.check_all(threshold_s=node_offline_threshold_s)
    for node, status in statuses.items():
        if status != 'online':
            logger.warning(f"Node {node} did not respond during boot: {status}")

    sm.transition(MODE_ACTIVE)

    if startup_tts:
        bat = store.get(TOPIC_POWER_BATTERY) or {}
        soc = bat.get('soc_percent', '?')
        offline = [n for n, s in statuses.items() if s != 'online']
        if offline:
            msg = f"VirtualHelmet online. Battery {soc} percent. Warning: {', '.join(offline)} node offline."
        else:
            msg = f"VirtualHelmet online. Battery {soc} percent. All systems ready."
        threading.Thread(target=speak, args=(msg,), daemon=True).start()

    logger.info("Orchestrator running")

    # --- Runtime loop ---
    last_status_publish = 0.0

    try:
        while True:
            now = time.time()

            # Publish system status every 30s
            if now - last_status_publish >= 30:
                node_statuses = node_mon.check_all(threshold_s=node_offline_threshold_s)
                mqtt.publish(TOPIC_SYSTEM_STATUS, {
                    "nodes": node_statuses,
                    "mode": sm.current_mode,
                    "alerts": list(alert_mgr.active_alerts),
                    "timestamp": now,
                })
                last_status_publish = now

                # Check for offline nodes → alert
                if any(s == 'offline' for s in node_statuses.values()):
                    alert_mgr.trigger('node_offline')
                else:
                    alert_mgr.clear('node_offline')

            # Re-speak critical alerts
            alert_mgr.repeat_critical()

            await asyncio.sleep(5)

    except asyncio.CancelledError:
        pass
    finally:
        mqtt.disconnect()
        logger.info("Orchestrator stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
