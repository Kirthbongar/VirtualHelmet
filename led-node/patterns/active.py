def run(num_leds, color, brightness_pct, max_brightness):
    """Steady solid color. Single frame, repeating."""
    scale = min(brightness_pct, max_brightness) / 100
    r, g, b = [int(c * scale) for c in color]
    colors = [(r, g, b)] * num_leds
    while True:
        yield (colors, 100)
