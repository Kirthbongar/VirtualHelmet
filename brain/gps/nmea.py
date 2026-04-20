import pynmea2
import logging

logger = logging.getLogger(__name__)


def parse_gga(sentence: str) -> dict | None:
    try:
        msg = pynmea2.parse(sentence)
        if not isinstance(msg, pynmea2.types.talker.GGA):
            return None
        if msg.latitude is None or msg.longitude is None:
            return None
        return {
            "lat":         float(msg.latitude),
            "lon":         float(msg.longitude),
            "altitude_m":  float(msg.altitude) if msg.altitude else 0.0,
            "fix_quality": int(msg.gps_qual) if msg.gps_qual else 0,
            "satellites":  int(msg.num_sats) if msg.num_sats else 0,
        }
    except Exception:
        return None


def parse_rmc(sentence: str) -> dict | None:
    try:
        msg = pynmea2.parse(sentence)
        if not isinstance(msg, pynmea2.types.talker.RMC):
            return None
        return {
            "speed_kmh":   float(msg.spd_over_grnd) * 1.852 if msg.spd_over_grnd else 0.0,
            "heading_deg": float(msg.true_course) if msg.true_course else 0.0,
        }
    except Exception:
        return None
