import pygame

class BatteryElement:
    X, Y = 580, 10
    BAR_W, BAR_H = 200, 20

    def render(self, surface: pygame.Surface, data_store, theme: dict):
        from shared.constants import TOPIC_POWER_BATTERY
        data = data_store.get(TOPIC_POWER_BATTERY)
        freshness = data_store.is_stale(TOPIC_POWER_BATTERY)

        color = theme['primary'] if freshness == 'fresh' else (
            theme['secondary'] if freshness == 'stale' else theme.get('dim', (80, 80, 80))
        )

        font = theme['font_small']

        if data is None or freshness == 'offline':
            text = font.render("BAT: ----", True, theme.get('dim', (80, 80, 80)))
            surface.blit(text, (self.X, self.Y))
            return

        soc = data.get('soc_percent', 0)
        eta = data.get('eta_minutes', 0)
        charging = data.get('charging', False)

        # Draw battery outline
        outline_rect = pygame.Rect(self.X, self.Y, self.BAR_W, self.BAR_H)
        pygame.draw.rect(surface, color, outline_rect, 2)

        # Fill bar proportional to SOC
        fill_w = int(self.BAR_W * soc / 100)
        if fill_w > 0:
            fill_color = theme['primary'] if soc > 20 else theme['alert'] if soc > 10 else theme['critical']
            fill_rect = pygame.Rect(self.X + 2, self.Y + 2, fill_w - 4, self.BAR_H - 4)
            pygame.draw.rect(surface, fill_color, fill_rect)

        # SOC text
        charge_sym = "+" if charging else ""
        label = f"{charge_sym}{soc}%  {eta}min"
        text = font.render(label, True, color)
        surface.blit(text, (self.X, self.Y + self.BAR_H + 2))
