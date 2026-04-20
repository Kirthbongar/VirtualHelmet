"""QMC5883L compass sensor — I2C 0x0D via smbus2."""

import logging
import math

logger = logging.getLogger(__name__)

_I2C_ADDRESS = 0x0D
_REG_DATA = 0x00
_REG_CTRL1 = 0x09
_CTRL1_VALUE = 0x0D  # continuous mode, 200Hz, 8G, 512 OSR


class Compass:
    """Reads heading from a QMC5883L magnetometer."""

    def __init__(self, declination_deg: float = 0.0, i2c_bus: int = 1) -> None:
        self._declination = declination_deg
        self._bus = None
        try:
            import smbus2
            self._bus = smbus2.SMBus(i2c_bus)
            self._bus.write_byte_data(_I2C_ADDRESS, _REG_CTRL1, _CTRL1_VALUE)
            logger.info("QMC5883L initialised on bus %d address 0x%02X", i2c_bus, _I2C_ADDRESS)
        except Exception as exc:
            logger.warning("Failed to initialise QMC5883L: %s", exc)

    def read(self) -> float:
        """Return heading in degrees [0, 360). Returns 0.0 on error."""
        if self._bus is None:
            return 0.0
        try:
            data = self._bus.read_i2c_block_data(_I2C_ADDRESS, _REG_DATA, 6)

            x = data[0] + data[1] * 256
            y = data[2] + data[3] * 256
            z = data[4] + data[5] * 256  # noqa: F841 — reserved for future tilt compensation

            if x > 32767:
                x -= 65536
            if y > 32767:
                y -= 65536
            if z > 32767:
                z -= 65536

            heading = math.atan2(float(y), float(x)) * 180.0 / math.pi
            heading += self._declination

            if heading < 0.0:
                heading += 360.0
            elif heading >= 360.0:
                heading -= 360.0

            return heading
        except Exception as exc:
            logger.warning("QMC5883L read error: %s", exc)
            return 0.0
