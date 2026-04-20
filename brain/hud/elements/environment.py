import pygame

class EnvironmentElement:
    X, Y = 10, 410

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_SENSORS_ENVIRONMENT
        data = data_store.get(TOPIC_SENSORS_ENVIRONMENT)
        freshness = data_store.is_stale(TOPIC_SENSORS_ENVIRONMENT)
        font = theme['font_small']
        dim = theme.get('dim', (80, 80, 80))
        color = theme['primary'] if freshness == 'fresh' else (theme['secondary'] if freshness == 'stale' else dim)

        if data is None or freshness == 'offline':
            text = font.render("TEMP: ----  HUM: ----", True, dim)
        else:
            temp_f = data.get('temperature_f', 0.0)
            hum = data.get('humidity_pct', 0.0)
            text = font.render(f"TEMP: {temp_f:.1f}°F  HUM: {hum:.0f}%", True, color)
        surface.blit(text, (self.X, self.Y))
