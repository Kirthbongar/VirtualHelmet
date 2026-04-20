import serial
import logging

logger = logging.getLogger(__name__)

class TFminiS:
    HEADER = 0x59

    def __init__(self, port: str, baudrate: int = 115200, min_strength: int = 100):
        self.port = port
        self.baudrate = baudrate
        self.min_strength = min_strength
        self._serial = None

    def open(self):
        self._serial = serial.Serial(self.port, self.baudrate, timeout=1)

    def close(self):
        if self._serial and self._serial.is_open:
            self._serial.close()

    def read_frame(self) -> dict:
        """Read one valid 9-byte frame. Returns dict with distance_m, distance_ft, strength, valid."""
        if not self._serial or not self._serial.is_open:
            raise IOError("Serial port not open")

        # Sync to frame header (0x59 0x59)
        while True:
            b = self._serial.read(1)
            if not b:
                raise TimeoutError("TFmini read timeout")
            if b[0] == self.HEADER:
                b2 = self._serial.read(1)
                if b2 and b2[0] == self.HEADER:
                    break

        # Read remaining 7 bytes
        rest = self._serial.read(7)
        if len(rest) < 7:
            return {"distance_m": 0, "distance_ft": 0, "strength": 0, "valid": False}

        frame = bytes([self.HEADER, self.HEADER]) + rest
        # Validate checksum
        checksum = sum(frame[:8]) % 256
        if checksum != frame[8]:
            logger.debug(f"TFmini checksum mismatch: {checksum} != {frame[8]}")
            return {"distance_m": 0, "distance_ft": 0, "strength": 0, "valid": False}

        dist_cm = frame[2] + frame[3] * 256
        strength = frame[4] + frame[5] * 256
        distance_m = dist_cm / 100.0
        distance_ft = distance_m * 3.28084
        valid = strength >= self.min_strength

        return {
            "distance_m": round(distance_m, 2),
            "distance_ft": round(distance_ft, 2),
            "strength": strength,
            "valid": valid
        }
