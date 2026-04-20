import logging

logger = logging.getLogger(__name__)

# Valid mode transitions
VALID_TRANSITIONS = {
    'boot':       {'active', 'idle'},
    'idle':       {'active', 'alert'},
    'active':     {'idle', 'power_save', 'alert'},
    'power_save': {'active', 'alert'},
    'alert':      {'active', 'idle', 'power_save'},
}

class StateMachine:
    def __init__(self, mqtt, initial_mode: str = 'boot'):
        self._mqtt = mqtt
        self._mode = initial_mode
        self._publish_mode()

    def _publish_mode(self):
        from shared.constants import TOPIC_SYSTEM_MODE
        self._mqtt.publish(TOPIC_SYSTEM_MODE, {"mode": self._mode})

    def _apply_led_effects(self, mode: str):
        from shared.constants import TOPIC_LEDS_EYES, TOPIC_LEDS_ACCENT, TOPIC_LEDS_ALERT, TOPIC_HUD_OVERLAY
        if mode == 'active':
            payload = {"color": [0, 180, 255], "brightness": 60, "pattern": "active"}
            self._mqtt.publish(TOPIC_LEDS_EYES, payload)
            self._mqtt.publish(TOPIC_LEDS_ACCENT, payload)
        elif mode == 'power_save':
            payload = {"brightness": 30, "pattern": "idle"}
            self._mqtt.publish(TOPIC_LEDS_EYES, payload)
            self._mqtt.publish(TOPIC_LEDS_ACCENT, payload)
            self._mqtt.publish(TOPIC_HUD_OVERLAY, {"brightness": 30})
        elif mode == 'idle':
            payload = {"color": [0, 100, 200], "brightness": 40, "pattern": "idle"}
            self._mqtt.publish(TOPIC_LEDS_EYES, payload)
            self._mqtt.publish(TOPIC_LEDS_ACCENT, payload)
        elif mode == 'alert':
            self._mqtt.publish(TOPIC_LEDS_ALERT, {"type": "alert", "active": True})

    def transition(self, new_mode: str) -> bool:
        allowed = VALID_TRANSITIONS.get(self._mode, set())
        if new_mode not in allowed:
            logger.warning(f"Invalid mode transition: {self._mode} -> {new_mode}")
            return False
        logger.info(f"Mode transition: {self._mode} -> {new_mode}")
        self._mode = new_mode
        self._publish_mode()
        self._apply_led_effects(new_mode)
        return True

    @property
    def current_mode(self) -> str:
        return self._mode
