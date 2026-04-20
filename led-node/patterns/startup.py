def run(num_leds, color, brightness_pct, max_brightness):
    """Sweep: LEDs turn on one by one from 0 to N, then hold."""
    scale = min(brightness_pct, max_brightness) / 100
    r, g, b = [int(c * scale) for c in color]
    colors = [(0, 0, 0)] * num_leds
    for i in range(num_leds):
        colors = colors[:]
        colors[i] = (r, g, b)
        yield (colors, 30)
    final = [(r, g, b)] * num_leds
    while True:
        yield (final, 100)
