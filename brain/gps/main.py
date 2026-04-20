import sys
import os
import asyncio
import serial
import json
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.mqtt_client import MQTTClient
from shared.constants import (
    TOPIC_GPS_POSITION,
    TOPIC_GPS_WAYPOINTS,
    TOPIC_VOICE_COMMANDS,
    TOPIC_SYSTEM_HEARTBEAT,
    NODE_BRAIN,
)
from shared.config_loader import load_config
from brain.gps.nmea import parse_gga, parse_rmc
from brain.gps.waypoints import WaypointStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'brain.yaml')

_position = {}


def _handle_voice_command(client, userdata, message):
    global _position
    try:
        payload = json.loads(message.payload.decode())
        command = payload.get("command", "")
        store: WaypointStore = userdata["waypoint_store"]

        if command == "mark_waypoint":
            lat = _position.get("lat")
            lon = _position.get("lon")
            if lat is not None and lon is not None:
                name = f"wp_{int(time.time())}"
                store.add(name, lat, lon)
                logger.info(f"Waypoint marked: {name} ({lat}, {lon})")
                client.publish(TOPIC_GPS_WAYPOINTS, {"waypoints": store.list_all()})
            else:
                logger.warning("mark_waypoint: no valid GPS fix")

        elif command == "list_waypoints":
            client.publish(TOPIC_GPS_WAYPOINTS, {"waypoints": store.list_all()})

    except Exception as exc:
        logger.warning(f"Voice command handler error: {exc}")


async def run():
    global _position

    cfg = load_config(CONFIG_PATH)
    gps_cfg = cfg.get('gps', {})

    port          = gps_cfg.get('port', '/dev/ttyUSB0')
    baudrate      = gps_cfg.get('baud', 9600)
    waypoint_file = gps_cfg.get('waypoint_file', 'brain/gps/data/waypoints.json')

    # Resolve waypoint file path relative to repo root when not absolute
    if not os.path.isabs(waypoint_file):
        waypoint_file = os.path.join(
            os.path.dirname(__file__), '..', '..', waypoint_file
        )
    waypoint_file = os.path.normpath(waypoint_file)

    # Ensure data directory exists
    os.makedirs(os.path.dirname(waypoint_file), exist_ok=True)

    store = WaypointStore(waypoint_file)

    mqtt_cfg = cfg.get('mqtt', {})
    mqtt = MQTTClient(
        broker=mqtt_cfg.get('broker_host', 'localhost'),
        port=mqtt_cfg.get('broker_port', 1883),
        client_id="brain-gps",
    )
    mqtt.connect()
    mqtt.subscribe(TOPIC_VOICE_COMMANDS, _handle_voice_command, userdata={"waypoint_store": store})

    last_heartbeat = 0.0
    last_publish   = 0.0
    publish_interval = 1.0

    def open_serial():
        ser = serial.Serial(port, baudrate, timeout=2)
        logger.info(f"GPS serial opened on {port} at {baudrate} baud")
        return ser

    ser = None

    try:
        ser = open_serial()
    except Exception as exc:
        logger.warning(f"GPS serial open failed: {exc}")

    try:
        while True:
            # Read and parse NMEA sentences
            if ser and ser.is_open:
                try:
                    raw = ser.readline().decode('ascii', errors='replace').strip()
                    if raw.startswith('$'):
                        gga = parse_gga(raw)
                        if gga:
                            _position.update(gga)

                        rmc = parse_rmc(raw)
                        if rmc:
                            _position.update(rmc)
                except (serial.SerialException, OSError) as exc:
                    logger.warning(f"GPS serial error: {exc} — retrying in 5s")
                    try:
                        ser.close()
                    except Exception:
                        pass
                    ser = None
                    await asyncio.sleep(5)
                    try:
                        ser = open_serial()
                    except Exception as reopen_exc:
                        logger.warning(f"GPS serial reopen failed: {reopen_exc}")
                    continue
            else:
                # No serial; wait before retrying
                await asyncio.sleep(5)
                try:
                    ser = open_serial()
                except Exception as exc:
                    logger.warning(f"GPS serial open failed: {exc}")
                continue

            now = time.time()

            # Publish position at 1 Hz
            if now - last_publish >= publish_interval:
                if _position.get("fix_quality", 0) and _position.get("fix_quality", 0) > 0:
                    payload = {
                        "lat":         _position.get("lat", 0.0),
                        "lon":         _position.get("lon", 0.0),
                        "altitude_m":  _position.get("altitude_m", 0.0),
                        "fix_quality": _position.get("fix_quality", 0),
                        "satellites":  _position.get("satellites", 0),
                        "speed_kmh":   _position.get("speed_kmh", 0.0),
                        "heading_deg": _position.get("heading_deg", 0.0),
                        "timestamp":   now,
                    }
                else:
                    payload = {
                        "fix_quality": 0,
                        "timestamp":   now,
                    }
                mqtt.publish(TOPIC_GPS_POSITION, payload)
                last_publish = now

            # Heartbeat every 30s
            if now - last_heartbeat >= 30:
                mqtt.publish(TOPIC_SYSTEM_HEARTBEAT, {
                    "node":      "brain/gps",
                    "timestamp": now,
                })
                last_heartbeat = now

            await asyncio.sleep(0)

    finally:
        if ser and ser.is_open:
            ser.close()
        mqtt.disconnect()


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("brain/gps stopped")


if __name__ == "__main__":
    main()
