import logging
import sys
import os

logger = logging.getLogger(__name__)

# Import speak from audio mixer — lazy import to avoid circular deps
def _get_speak():
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from brain.audio.mixer import AudioMixer
        # speak is a module-level function set up in audio/main.py
        # Fall back to a no-op if audio service not running in same process
        import brain.audio.main as audio_main
        return audio_main.speak
    except Exception:
        logger.warning("Audio mixer not available — TTS disabled")
        return lambda text: logger.info(f"TTS (no audio): {text}")

_speak_fn = None

def _speak(text: str):
    global _speak_fn
    if _speak_fn is None:
        _speak_fn = _get_speak()
    try:
        _speak_fn(text)
    except Exception as e:
        logger.warning(f"TTS speak failed: {e}")

def confirm():
    _speak("Got it.")

def unknown():
    _speak("Sorry, I didn't catch that.")

def respond(template: str, **kwargs):
    text = template.format(**kwargs)
    _speak(text)
