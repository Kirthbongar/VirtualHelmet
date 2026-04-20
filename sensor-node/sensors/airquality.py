"""CCS811 air quality sensor — CO2 and TVOC via CircuitPython."""

import asyncio
import logging
import time

from shared.constants import TOPIC_SENSORS_AIRQUALITY

logger = logging.getLogger(__name__)

_WARMUP_SECONDS = 1200  # 20 minutes


async def run_airquality_task(mqtt_client, aq_cfg: dict) -> None:
    poll_interval = float(aq_cfg.get("poll_interval_s", 10))

    sensor = None
    start_time = time.time()

    try:
        import board
        import busio
        import adafruit_ccs811
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_ccs811.CCS811(i2c)
        logger.info("CCS811 initialised")
    except Exception as exc:
        logger.warning("Failed to initialise CCS811: %s", exc)

    while True:
        now = time.time()
        elapsed = now - start_time
        warming_up = elapsed < _WARMUP_SECONDS

        if warming_up:
            payload = {
                "co2_ppm": 0,
                "tvoc_ppb": 0,
                "warming_up": True,
                "timestamp": now,
            }
            try:
                mqtt_client.publish(TOPIC_SENSORS_AIRQUALITY, payload)
            except Exception as exc:
                logger.warning("Air quality MQTT publish failed (warmup): %s", exc)
        elif sensor is not None:
            try:
                if sensor.data_ready:
                    payload = {
                        "co2_ppm": sensor.eco2,
                        "tvoc_ppb": sensor.tvoc,
                        "warming_up": False,
                        "timestamp": now,
                    }
                    try:
                        mqtt_client.publish(TOPIC_SENSORS_AIRQUALITY, payload)
                    except Exception as exc:
                        logger.warning("Air quality MQTT publish failed: %s", exc)
            except Exception as exc:
                logger.warning("CCS811 read error: %s", exc)

        await asyncio.sleep(poll_interval)
