import pygame

class DistanceElement:
    X, Y = 500, 380

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_LIDAR_DISTANCE
        data = data_store.get(TOPIC_LIDAR_DISTANCE)
        freshness = data_store.is_stale(TOPIC_LIDAR_DISTANCE)
        font = theme['font_small']
        dim = theme.get('dim', (80, 80, 80))
        color = theme['primary'] if freshness == 'fresh' else (theme['secondary'] if freshness == 'stale' else dim)

        if data is None or freshness == 'offline':
            text = font.render("DIST: ----", True, dim)
        elif not data.get('valid', False):
            text = font.render("DIST: ---ft", True, theme.get('secondary', color))
        else:
            dist_ft = data.get('distance_ft', 0.0)
            text = font.render(f"DIST: {dist_ft:.1f}ft", True, color)
        surface.blit(text, (self.X, self.Y))
