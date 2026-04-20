import subprocess
import logging

logger = logging.getLogger(__name__)

class VolumeController:
    def __init__(self):
        self._pre_duck_volume = 70

    def set_volume(self, percent: int):
        percent = max(0, min(100, percent))
        try:
            subprocess.run(['amixer', 'sset', 'Master', f'{percent}%'],
                          capture_output=True, check=True)
            logger.debug(f"Volume set to {percent}%")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Volume set failed: {e}")

    def get_volume(self) -> int:
        try:
            result = subprocess.run(['amixer', 'sget', 'Master'],
                                   capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if '%' in line:
                    val = line.split('[')[1].split('%')[0]
                    return int(val)
        except (subprocess.CalledProcessError, IndexError, ValueError) as e:
            logger.warning(f"get_volume failed: {e}")
        return 70

    def duck(self, percent: int):
        self._pre_duck_volume = self.get_volume()
        self.set_volume(percent)

    def unduck(self):
        self.set_volume(self._pre_duck_volume)
