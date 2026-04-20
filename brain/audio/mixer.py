import subprocess
import logging
import os

logger = logging.getLogger(__name__)

class AudioMixer:
    def __init__(self, volume_controller, tts_duck_pct: int, piper_model_path: str):
        self.volume = volume_controller
        self.duck_pct = tts_duck_pct
        self.piper_model = piper_model_path

    def speak(self, text: str):
        """Duck music, synthesize TTS with Piper, play, then unduck."""
        self.volume.duck(self.duck_pct)
        try:
            piper_cmd = ['piper', '--model', self.piper_model, '--output_raw']
            aplay_cmd = ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-']
            piper_proc = subprocess.Popen(
                piper_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            aplay_proc = subprocess.Popen(
                aplay_cmd,
                stdin=piper_proc.stdout,
                stderr=subprocess.DEVNULL
            )
            piper_proc.stdin.write(text.encode('utf-8'))
            piper_proc.stdin.close()
            piper_proc.stdout.close()
            aplay_proc.wait()
            piper_proc.wait()
        except Exception as e:
            logger.warning(f"TTS speak failed: {e}")
        finally:
            self.volume.unduck()
