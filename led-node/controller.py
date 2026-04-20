import threading
import time
import logging
from rpi_ws281x import PixelStrip, Color

logger = logging.getLogger(__name__)


class LEDController:
    def __init__(self, eyes_cfg, accent_cfg, max_brightness):
        self.max_brightness = max_brightness
        self._eyes_strip = PixelStrip(
            eyes_cfg['led_count'], eyes_cfg['gpio_pin'],
            800000, 10, False, max_brightness, 0
        )
        self._accent_strip = PixelStrip(
            accent_cfg['led_count'], accent_cfg['gpio_pin'],
            800000, 10, False, max_brightness, 1
        )
        self._eyes_strip.begin()
        self._accent_strip.begin()

        self._eyes_state = {
            'color': eyes_cfg['default_color'],
            'brightness': eyes_cfg['default_brightness'],
            'pattern': 'idle',
        }
        self._accent_state = {
            'color': accent_cfg['default_color'],
            'brightness': accent_cfg['default_brightness'],
            'pattern': 'idle',
        }
        self._alert_active = False
        self._alert_type = None

        self._lock = threading.Lock()
        self._eyes_thread = None
        self._accent_thread = None
        self._eyes_stop = threading.Event()
        self._accent_stop = threading.Event()

        self._start_pattern('eyes', 'startup')
        self._start_pattern('accent', 'startup')

    def _get_strip(self, target):
        return self._eyes_strip if target == 'eyes' else self._accent_strip

    def _get_state(self, target):
        return self._eyes_state if target == 'eyes' else self._accent_state

    def _run_pattern(self, strip, pattern_name, color, brightness, stop_event):
        from led_node.patterns import idle, active, alert, low_battery, startup
        pattern_map = {
            'idle': idle,
            'active': active,
            'alert': alert,
            'low_battery': low_battery,
            'startup': startup,
        }
        mod = pattern_map.get(pattern_name, idle)
        gen = mod.run(strip.numPixels(), color, brightness, self.max_brightness)
        for colors, sleep_ms in gen:
            if stop_event.is_set():
                break
            for i, (r, g, b) in enumerate(colors):
                strip.setPixelColor(i, Color(r, g, b))
            strip.show()
            time.sleep(sleep_ms / 1000)

    def _start_pattern(self, target, pattern_name):
        state = self._get_state(target)
        strip = self._get_strip(target)
        stop = threading.Event()
        if target == 'eyes':
            if self._eyes_thread and self._eyes_thread.is_alive():
                self._eyes_stop.set()
                self._eyes_thread.join(timeout=1)
            self._eyes_stop = stop
            self._eyes_thread = threading.Thread(
                target=self._run_pattern,
                args=(strip, pattern_name, state['color'], state['brightness'], stop),
                daemon=True,
            )
            self._eyes_thread.start()
        else:
            if self._accent_thread and self._accent_thread.is_alive():
                self._accent_stop.set()
                self._accent_thread.join(timeout=1)
            self._accent_stop = stop
            self._accent_thread = threading.Thread(
                target=self._run_pattern,
                args=(strip, pattern_name, state['color'], state['brightness'], stop),
                daemon=True,
            )
            self._accent_thread.start()

    def set_color_pattern(self, target, color, brightness, pattern):
        state = self._get_state(target)
        state['color'] = color
        state['brightness'] = min(brightness, self.max_brightness)
        state['pattern'] = pattern
        if not self._alert_active:
            self._start_pattern(target, pattern)

    def set_alert(self, alert_type, active):
        self._alert_active = active
        self._alert_type = alert_type if active else None
        if active:
            self._start_pattern('eyes', 'alert')
            self._start_pattern('accent', 'alert')
        else:
            self._start_pattern('eyes', self._eyes_state['pattern'])
            self._start_pattern('accent', self._accent_state['pattern'])

    def clear(self):
        for strip in [self._eyes_strip, self._accent_strip]:
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(0, 0, 0))
            strip.show()
