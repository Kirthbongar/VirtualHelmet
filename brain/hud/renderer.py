import pygame
import logging
import json

logger = logging.getLogger(__name__)

from brain.hud.elements.battery import BatteryElement
from brain.hud.elements.compass import CompassElement
from brain.hud.elements.level import LevelElement
from brain.hud.elements.environment import EnvironmentElement
from brain.hud.elements.airquality import AirQualityElement
from brain.hud.elements.distance import DistanceElement
from brain.hud.elements.gps import GpsElement
from brain.hud.elements.status import StatusElement
from brain.hud.elements.alerts import AlertsElement

THEMES = {
    'halo_green': {
        'background': (0, 0, 0),
        'primary': (0, 255, 140),
        'secondary': (0, 180, 100),
        'alert': (255, 200, 0),
        'critical': (255, 50, 0),
        'dim': (40, 80, 60),
    },
    'night_mode': {
        'background': (0, 0, 0),
        'primary': (180, 60, 0),
        'secondary': (120, 40, 0),
        'alert': (200, 100, 0),
        'critical': (255, 50, 0),
        'dim': (60, 20, 0),
    },
    'high_contrast': {
        'background': (0, 0, 0),
        'primary': (255, 255, 255),
        'secondary': (180, 180, 180),
        'alert': (255, 220, 0),
        'critical': (255, 0, 0),
        'dim': (80, 80, 80),
    },
}

class HUDRenderer:
    def __init__(self, data_store, config: dict):
        hud_cfg = config.get('hud', {})
        res = hud_cfg.get('resolution', [800, 480])
        self.width, self.height = res[0], res[1]
        self.target_fps = hud_cfg.get('fps', 30)
        self.theme_name = hud_cfg.get('theme', 'halo_green')
        font_path = hud_cfg.get('font_path', None)

        self.data_store = data_store

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.display.set_caption("VirtualHelmet HUD")
        self.clock = pygame.time.Clock()

        # Load fonts
        if font_path:
            try:
                font_small = pygame.font.Font(font_path, 16)
                font_medium = pygame.font.Font(font_path, 22)
            except Exception:
                logger.warning(f"Font not found at {font_path}, using default")
                font_small = pygame.font.SysFont('monospace', 16)
                font_medium = pygame.font.SysFont('monospace', 22)
        else:
            font_small = pygame.font.SysFont('monospace', 16)
            font_medium = pygame.font.SysFont('monospace', 22)

        self._fonts = {'font_small': font_small, 'font_medium': font_medium}
        self._set_theme(self.theme_name)

        self.elements = [
            StatusElement(),
            BatteryElement(),
            CompassElement(),
            LevelElement(),
            EnvironmentElement(),
            AirQualityElement(),
            DistanceElement(),
            GpsElement(),
            AlertsElement(),
        ]

    def _set_theme(self, name: str):
        theme = THEMES.get(name, THEMES['halo_green']).copy()
        theme.update(self._fonts)
        self.theme = theme
        self.theme_name = name

    def handle_overlay(self, payload: dict):
        new_theme = payload.get('theme')
        if new_theme and new_theme in THEMES:
            self._set_theme(new_theme)
            logger.info(f"Theme changed to: {new_theme}")

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            self.screen.fill(self.theme['background'])

            for element in self.elements:
                try:
                    element.render(self.screen, self.data_store, self.theme)
                except Exception as e:
                    logger.warning(f"Element {element.__class__.__name__} render error: {e}")

            pygame.display.flip()
            self.clock.tick(self.target_fps)

        pygame.quit()
