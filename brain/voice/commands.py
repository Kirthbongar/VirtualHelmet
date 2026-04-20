import logging

logger = logging.getLogger(__name__)

COMMAND_MAP = {
    "lights on": "lights_on",
    "lights off": "lights_off",
    "status": "status",
    "battery": "battery",
    "distance": "distance",
    "mark waypoint": "mark_waypoint",
    "heading": "heading",
    "temperature": "temperature",
    "night mode": "night_mode",
    "power save": "power_save",
    "resume": "resume",
    "pause music": "music_pause",
    "play music": "music_play",
    "next song": "music_next",
    "volume up": "volume_up",
    "volume down": "volume_down",
    "shutdown": "shutdown",
}

def parse(text: str, confidence_threshold: float = 0.80) -> tuple:
    """
    Match recognized text to a command.
    Returns (command_id, confidence) or (None, 0.0).
    Strategy: exact substring match first (confidence 1.0), then token overlap score.
    """
    text_lower = text.lower().strip()

    # Exact substring match
    for phrase, command_id in COMMAND_MAP.items():
        if phrase in text_lower:
            return (command_id, 1.0)

    # Token overlap scoring
    text_tokens = set(text_lower.split())
    best_cmd = None
    best_score = 0.0

    for phrase, command_id in COMMAND_MAP.items():
        phrase_tokens = set(phrase.split())
        if not phrase_tokens:
            continue
        overlap = len(text_tokens & phrase_tokens)
        score = overlap / len(phrase_tokens)
        if score > best_score:
            best_score = score
            best_cmd = command_id

    if best_score >= confidence_threshold:
        return (best_cmd, best_score)

    return (None, 0.0)
