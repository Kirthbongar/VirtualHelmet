"""IMU sensor task — MPU-6050 via I2C 0x68, complementary filter for pitch/roll."""

import asyncio
import logging
import math
import time

from shared.constants import TOPIC_SENSORS_IMU

logger = logging.getLogger(__name__)

_I2C_ADDRESS = 0x68


async def run_imu_task(mqtt_client, imu_cfg: dict, compass) -> None:
    poll_hz = float(imu_cfg.get("poll_hz", 10))
    interval = 1.0 / poll_hz

    sensor = None
    try:
        from mpu6050 import mpu6050
        sensor = mpu6050(_I2C_ADDRESS)
    except Exception as exc:
        logger.warning("Failed to initialise MPU-6050: %s", exc)

    pitch = 0.0
    roll = 0.0
    last_time = time.time()

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now

        if sensor is not None:
            try:
                accel = sensor.get_accel_data()
                gyro = sensor.get_gyro_data()

                ax = accel["x"]
                ay = accel["y"]
                az = accel["z"]

                accel_pitch = math.atan2(ay, math.sqrt(ax * ax + az * az)) * 180.0 / math.pi
                accel_roll = math.atan2(-ax, az) * 180.0 / math.pi

                gyro_pitch_rate = gyro["x"]
                gyro_roll_rate = gyro["y"]
                gyro_yaw_rate = gyro["z"]

                pitch = 0.98 * (pitch + gyro_pitch_rate * dt) + 0.02 * accel_pitch
                roll = 0.98 * (roll + gyro_roll_rate * dt) + 0.02 * accel_roll
                yaw = gyro_yaw_rate

                try:
                    heading_deg = compass.read()
                except Exception as exc:
                    logger.warning("Compass read failed: %s", exc)
                    heading_deg = 0.0

                payload = {
                    "yaw": round(yaw, 4),
                    "pitch": round(pitch, 4),
                    "roll": round(roll, 4),
                    "heading_deg": round(heading_deg, 2),
                    "timestamp": now,
                }

                try:
                    mqtt_client.publish(TOPIC_SENSORS_IMU, payload)
                except Exception as exc:
                    logger.warning("IMU MQTT publish failed: %s", exc)

            except Exception as exc:
                logger.warning("IMU read error: %s", exc)

        await asyncio.sleep(interval)
