import pygame

class GpsElement:
    X, Y = 10, 440

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_GPS_POSITION
        data = data_store.get(TOPIC_GPS_POSITION)
        freshness = data_store.is_stale(TOPIC_GPS_POSITION)
        font = theme['font_small']
        dim = theme.get('dim', (80, 80, 80))
        color = theme['primary'] if freshness == 'fresh' else (theme['secondary'] if freshness == 'stale' else dim)

        if data is None or freshness == 'offline':
            text = font.render("GPS: OFFLINE", True, dim)
        elif data.get('fix_quality', 0) == 0:
            text = font.render("GPS: ACQUIRING", True, theme.get('secondary', color))
        else:
            lat = data.get('lat', 0.0)
            lon = data.get('lon', 0.0)
            text = font.render(f"GPS: {lat:.5f}  {lon:.5f}", True, color)
        surface.blit(text, (self.X, self.Y))
