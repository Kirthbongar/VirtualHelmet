import time
import threading
import logging

logger = logging.getLogger(__name__)

ALERT_MESSAGES = {
    "low_battery":       "Warning. Battery below twenty percent.",
    "critical_battery":  "Critical. Battery below ten percent. Find power soon.",
    "shutdown_battery":  "Battery critically low. Initiating shutdown.",
    "co2_warning":       "Warning. CO2 levels elevated.",
    "co2_critical":      "Alert. CO2 levels critical. Move to fresh air.",
    "temp_warning":      "Warning. High temperature detected.",
    "node_offline":      "Warning. A helmet node has gone offline.",
}

class AlertManager:
    def __init__(self, mqtt, speak_fn, repeat_interval_s: float = 60.0):
        self._mqtt = mqtt
        self._speak = speak_fn
        self._repeat_interval_s = repeat_interval_s
        self._active = {}        # alert_type -> last_spoken float
        self._lock = threading.Lock()

    def trigger(self, alert_type: str):
        from shared.constants import TOPIC_LEDS_ALERT, TOPIC_HUD_OVERLAY
        with self._lock:
            now = time.time()
            already_active = alert_type in self._active
            self._active[alert_type] = self._active.get(alert_type, 0)

        if not already_active:
            # First trigger — publish LED alert and HUD
            self._mqtt.publish(TOPIC_LEDS_ALERT, {"type": alert_type, "active": True})
            msg = ALERT_MESSAGES.get(alert_type, f"Alert: {alert_type}")
            self._speak_async(msg)
            with self._lock:
                self._active[alert_type] = now

    def clear(self, alert_type: str):
        from shared.constants import TOPIC_LEDS_ALERT
        with self._lock:
            if alert_type in self._active:
                del self._active[alert_type]
        self._mqtt.publish(TOPIC_LEDS_ALERT, {"type": alert_type, "active": False})

    def repeat_critical(self):
        """Call periodically — re-speaks active critical alerts if interval elapsed."""
        critical_types = {"critical_battery", "co2_critical"}
        now = time.time()
        with self._lock:
            to_repeat = [
                (k, v) for k, v in self._active.items()
                if k in critical_types and (now - v) >= self._repeat_interval_s
            ]
        for alert_type, _ in to_repeat:
            msg = ALERT_MESSAGES.get(alert_type, alert_type)
            self._speak_async(msg)
            with self._lock:
                if alert_type in self._active:
                    self._active[alert_type] = now

    def _speak_async(self, text: str):
        t = threading.Thread(target=self._speak, args=(text,), daemon=True)
        t.start()

    @property
    def active_alerts(self) -> set:
        with self._lock:
            return set(self._active.keys())
