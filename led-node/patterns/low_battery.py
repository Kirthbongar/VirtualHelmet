import math


def run(num_leds, color=(255, 140, 0), brightness_pct=60, max_brightness=80):
    """Slow amber pulse over ~4 seconds."""
    period = 4.0
    while True:
        for step in range(60):
            t = step / 60
            factor = (math.sin(t * 2 * math.pi - math.pi / 2) + 1) / 2
            scale = (0.2 + 0.8 * factor) * (min(brightness_pct, max_brightness) / 100)
            r = int(255 * scale)
            g = int(140 * scale)
            b = 0
            colors = [(r, g, b)] * num_leds
            yield (colors, int(period * 1000 / 60))
