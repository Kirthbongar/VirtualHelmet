"""BME280 environment sensor — temperature, humidity, pressure via I2C 0x76."""

import asyncio
import logging
import time

from shared.constants import TOPIC_SENSORS_ENVIRONMENT

logger = logging.getLogger(__name__)

_I2C_ADDRESS = 0x76
_I2C_BUS = 1


async def run_environment_task(mqtt_client, env_cfg: dict) -> None:
    poll_interval = float(env_cfg.get("poll_interval_s", 5))
    temp_offset = float(env_cfg.get("temperature_offset_c", 0.0))

    bus = None
    calibration_params = None
    try:
        import smbus2
        import bme280
        bus = smbus2.SMBus(_I2C_BUS)
        calibration_params = bme280.load_calibration_params(bus, _I2C_ADDRESS)
        logger.info("BME280 initialised at 0x%02X", _I2C_ADDRESS)
    except Exception as exc:
        logger.warning("Failed to initialise BME280: %s", exc)

    while True:
        if bus is not None and calibration_params is not None:
            try:
                import bme280
                data = bme280.sample(bus, _I2C_ADDRESS, calibration_params)

                temp_c = data.temperature + temp_offset
                temp_f = temp_c * 9.0 / 5.0 + 32.0

                payload = {
                    "temperature_c": round(temp_c, 2),
                    "temperature_f": round(temp_f, 2),
                    "humidity_pct": round(data.humidity, 2),
                    "pressure_hpa": round(data.pressure, 2),
                    "timestamp": time.time(),
                }

                try:
                    mqtt_client.publish(TOPIC_SENSORS_ENVIRONMENT, payload)
                except Exception as exc:
                    logger.warning("Environment MQTT publish failed: %s", exc)

            except Exception as exc:
                logger.warning("BME280 read error: %s", exc)

        await asyncio.sleep(poll_interval)
