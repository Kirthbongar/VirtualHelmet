import pygame

class AirQualityElement:
    X, Y = 500, 410

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_SENSORS_AIRQUALITY
        data = data_store.get(TOPIC_SENSORS_AIRQUALITY)
        freshness = data_store.is_stale(TOPIC_SENSORS_AIRQUALITY)
        font = theme['font_small']
        dim = theme.get('dim', (80, 80, 80))
        color = theme['primary'] if freshness == 'fresh' else (theme['secondary'] if freshness == 'stale' else dim)

        if data is None or freshness == 'offline':
            text = font.render("CO2: ----", True, dim)
        elif data.get('warming_up', True):
            text = font.render("CO2: WARMING", True, theme.get('secondary', color))
        else:
            co2 = data.get('co2_ppm', 0)
            co2_color = theme['critical'] if co2 > 2500 else theme['alert'] if co2 > 1500 else color
            text = font.render(f"CO2: {co2}ppm", True, co2_color)
        surface.blit(text, (self.X, self.Y))
