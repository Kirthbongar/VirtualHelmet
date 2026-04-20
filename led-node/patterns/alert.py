def run(num_leds, color=(255, 0, 0), brightness_pct=100, max_brightness=80):
    """Rapid red flash: 200ms on / 200ms off."""
    scale = min(brightness_pct, max_brightness) / 100
    on_colors = [(int(255 * scale), 0, 0)] * num_leds
    off_colors = [(0, 0, 0)] * num_leds
    while True:
        yield (on_colors, 200)
        yield (off_colors, 200)
