import math
import time


def run(num_leds, color, brightness_pct, max_brightness):
    """Slow blue-white breathing pulse over ~3 seconds. Generator yields (colors, sleep_ms)."""
    base_r, base_g, base_b = color
    period = 3.0
    while True:
        for step in range(60):
            t = step / 60
            factor = (math.sin(t * 2 * math.pi - math.pi / 2) + 1) / 2  # 0..1
            scale = (0.3 + 0.7 * factor) * (min(brightness_pct, max_brightness) / 100)
            r = int(base_r * scale)
            g = int(base_g * scale)
            b = int(base_b * scale)
            colors = [(r, g, b)] * num_leds
            yield (colors, int(period * 1000 / 60))
