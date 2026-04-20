import pygame

class StatusElement:
    X, Y = 10, 10

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_SENSORS_IMU, TOPIC_POWER_BATTERY, TOPIC_GPS_POSITION
        font = theme['font_small']

        indicators = [
            ('SNS', TOPIC_SENSORS_IMU),
            ('PWR', TOPIC_POWER_BATTERY),
            ('GPS', TOPIC_GPS_POSITION),
        ]

        x = self.X
        for label, topic in indicators:
            freshness = data_store.is_stale(topic)
            if freshness == 'fresh':
                color = theme['primary']
            elif freshness == 'stale':
                color = theme['alert']
            else:
                color = theme['critical']
            text = font.render(f"[{label}]", True, color)
            surface.blit(text, (x, self.Y))
            x += text.get_width() + 8
