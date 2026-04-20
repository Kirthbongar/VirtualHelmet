import pygame
import time

class AlertsElement:
    CX, CY = 400, 240

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_POWER_BATTERY, TOPIC_SENSORS_AIRQUALITY
        font = theme['font_medium']

        alerts = []

        bat = data_store.get(TOPIC_POWER_BATTERY)
        if bat and bat.get('soc_percent', 100) <= 10:
            alerts.append("LOW BATTERY")

        aq = data_store.get(TOPIC_SENSORS_AIRQUALITY)
        if aq and not aq.get('warming_up', True) and aq.get('co2_ppm', 0) > 2500:
            alerts.append("HIGH CO2")

        if not alerts:
            return

        # Flash: visible on even half-seconds
        if int(time.time() * 2) % 2 == 0:
            for i, msg in enumerate(alerts):
                text = font.render(msg, True, theme['critical'])
                rect = text.get_rect(center=(self.CX, self.CY + i * 30))
                surface.blit(text, rect)
