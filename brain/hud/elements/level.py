import pygame

class LevelElement:
    X, Y = 10, 380

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_SENSORS_IMU
        data = data_store.get(TOPIC_SENSORS_IMU)
        freshness = data_store.is_stale(TOPIC_SENSORS_IMU)
        font = theme['font_small']
        dim = theme.get('dim', (80, 80, 80))
        color = theme['primary'] if freshness == 'fresh' else (theme['secondary'] if freshness == 'stale' else dim)

        if data is None or freshness == 'offline':
            text = font.render("P: ----  R: ----", True, dim)
        else:
            pitch = data.get('pitch', 0.0)
            roll = data.get('roll', 0.0)
            text = font.render(f"P: {pitch:+.1f}°  R: {roll:+.1f}°", True, color)
        surface.blit(text, (self.X, self.Y))
