import subprocess
import threading
import logging

logger = logging.getLogger(__name__)

class CommandRouter:
    def __init__(self, mqtt, data_store, state_machine, speak_fn):
        self._mqtt = mqtt
        self._store = data_store
        self._sm = state_machine
        self._speak = speak_fn

    def route(self, command: str):
        """Route a command_id string to the appropriate action. Non-blocking."""
        handler = getattr(self, f'_cmd_{command}', None)
        if handler is None:
            logger.warning(f"No handler for command: {command}")
            return
        t = threading.Thread(target=handler, daemon=True)
        t.start()

    # --- LED commands ---
    def _cmd_lights_on(self):
        from shared.constants import TOPIC_LEDS_EYES, TOPIC_LEDS_ACCENT
        payload = {"color": [0, 180, 255], "brightness": 60, "pattern": "active"}
        self._mqtt.publish(TOPIC_LEDS_EYES, payload)
        self._mqtt.publish(TOPIC_LEDS_ACCENT, payload)

    def _cmd_lights_off(self):
        from shared.constants import TOPIC_LEDS_EYES, TOPIC_LEDS_ACCENT
        payload = {"color": [0, 0, 0], "brightness": 0, "pattern": "active"}
        self._mqtt.publish(TOPIC_LEDS_EYES, payload)
        self._mqtt.publish(TOPIC_LEDS_ACCENT, payload)

    # --- Status/query commands ---
    def _cmd_status(self):
        from shared.constants import TOPIC_POWER_BATTERY, TOPIC_SENSORS_ENVIRONMENT, TOPIC_SENSORS_IMU
        bat = self._store.get(TOPIC_POWER_BATTERY) or {}
        env = self._store.get(TOPIC_SENSORS_ENVIRONMENT) or {}
        imu = self._store.get(TOPIC_SENSORS_IMU) or {}
        soc = bat.get('soc_percent', '?')
        temp_f = env.get('temperature_f', '?')
        heading = imu.get('heading_deg', '?')
        self._speak(f"Battery {soc} percent. Temperature {temp_f:.0f} degrees. Heading {heading:.0f} degrees." if isinstance(temp_f, float) else "Status unavailable.")

    def _cmd_battery(self):
        from shared.constants import TOPIC_POWER_BATTERY
        bat = self._store.get(TOPIC_POWER_BATTERY) or {}
        soc = bat.get('soc_percent')
        eta = bat.get('eta_minutes')
        if soc is None:
            self._speak("Battery data unavailable.")
        else:
            self._speak(f"Battery at {soc} percent. Estimated {eta} minutes remaining.")

    def _cmd_distance(self):
        from shared.constants import TOPIC_LIDAR_DISTANCE
        data = self._store.get(TOPIC_LIDAR_DISTANCE) or {}
        if not data.get('valid', False):
            self._speak("Distance reading unavailable.")
        else:
            ft = data.get('distance_ft', 0)
            self._speak(f"Distance {ft:.1f} feet.")

    def _cmd_heading(self):
        from shared.constants import TOPIC_SENSORS_IMU
        data = self._store.get(TOPIC_SENSORS_IMU) or {}
        heading = data.get('heading_deg')
        if heading is None:
            self._speak("Heading unavailable.")
        else:
            self._speak(f"Heading {heading:.0f} degrees.")

    def _cmd_temperature(self):
        from shared.constants import TOPIC_SENSORS_ENVIRONMENT
        data = self._store.get(TOPIC_SENSORS_ENVIRONMENT) or {}
        temp_f = data.get('temperature_f')
        hum = data.get('humidity_pct')
        if temp_f is None:
            self._speak("Temperature unavailable.")
        else:
            self._speak(f"Temperature {temp_f:.0f} degrees Fahrenheit. Humidity {hum:.0f} percent.")

    # --- Mode commands ---
    def _cmd_night_mode(self):
        from shared.constants import TOPIC_HUD_OVERLAY, MODE_POWER_SAVE
        self._sm.transition(MODE_POWER_SAVE)
        self._mqtt.publish(TOPIC_HUD_OVERLAY, {"theme": "night_mode"})

    def _cmd_power_save(self):
        from shared.constants import MODE_POWER_SAVE
        self._sm.transition(MODE_POWER_SAVE)

    def _cmd_resume(self):
        from shared.constants import MODE_ACTIVE
        self._sm.transition(MODE_ACTIVE)
        from shared.constants import TOPIC_HUD_OVERLAY
        self._mqtt.publish(TOPIC_HUD_OVERLAY, {"theme": "halo_green"})

    # --- Music/audio pass-through — audio service handles these via TOPIC_VOICE_COMMANDS ---
    def _cmd_music_pause(self): pass
    def _cmd_music_play(self): pass
    def _cmd_music_next(self): pass
    def _cmd_volume_up(self): pass
    def _cmd_volume_down(self): pass

    # --- Shutdown ---
    def _cmd_shutdown(self):
        self._speak("Shutting down. Goodbye.")
        import time; time.sleep(3)
        subprocess.run(["sudo", "shutdown", "-h", "now"])
