import pygame

class CompassElement:
    X, Y = 10, 40

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_SENSORS_IMU
        data = data_store.get(TOPIC_SENSORS_IMU)
        freshness = data_store.is_stale(TOPIC_SENSORS_IMU)
        font = theme['font_medium']
        dim = theme.get('dim', (80, 80, 80))
        color = theme['primary'] if freshness == 'fresh' else (theme['secondary'] if freshness == 'stale' else dim)

        if data is None or freshness == 'offline':
            text = font.render("HDG: ----", True, dim)
        else:
            heading = data.get('heading_deg', 0.0)
            directions = ['N','NE','E','SE','S','SW','W','NW','N']
            idx = int((heading + 22.5) / 45) % 8
            cardinal = directions[idx]
            text = font.render(f"HDG: {heading:.0f}° {cardinal}", True, color)
        surface.blit(text, (self.X, self.Y))
