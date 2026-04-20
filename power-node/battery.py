import logging
from ina219 import INA219

logger = logging.getLogger(__name__)

_SOC_TABLE = [
    (8.4, 100),
    (8.0, 85),
    (7.6, 60),
    (7.2, 35),
    (6.8, 10),
    (6.0, 0),
]


def _voltage_to_soc(voltage: float) -> int:
    if voltage >= _SOC_TABLE[0][0]:
        return 100
    if voltage <= _SOC_TABLE[-1][0]:
        return 0
    for i in range(len(_SOC_TABLE) - 1):
        v_high, soc_high = _SOC_TABLE[i]
        v_low, soc_low = _SOC_TABLE[i + 1]
        if v_low <= voltage <= v_high:
            ratio = (voltage - v_low) / (v_high - v_low)
            return round(soc_low + ratio * (soc_high - soc_low))
    return 0


class BatteryMonitor:
    def __init__(self, shunt_ohms: float, capacity_wh: float):
        self._capacity_wh = capacity_wh
        self._ina = INA219(shunt_ohms=shunt_ohms, address=0x40)
        self._ina.configure()

    def read(self) -> dict:
        try:
            voltage_v = self._ina.voltage()
            current_ma = self._ina.current()
            power_w = self._ina.power() / 1000.0
        except Exception as exc:
            logger.error("INA219 read failed: %s", exc)
            raise

        soc_pct = _voltage_to_soc(voltage_v)
        remaining_wh = self._capacity_wh * (soc_pct / 100)

        if power_w < 0.1:
            eta_minutes = 999
        else:
            eta_minutes = int((remaining_wh / power_w) * 60)

        return {
            "voltage_v": voltage_v,
            "current_ma": current_ma,
            "power_w": power_w,
            "soc_percent": soc_pct,
            "eta_minutes": eta_minutes,
            "charging": current_ma < 0,
        }
