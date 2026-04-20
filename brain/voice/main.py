import sys
import os
import json
import asyncio
import logging
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.mqtt_client import MQTTClient
from shared.constants import TOPIC_VOICE_COMMANDS, TOPIC_SYSTEM_MODE, TOPIC_SYSTEM_HEARTBEAT, NODE_BRAIN
from shared.config_loader import load_config
from brain.voice.recognizer import VoiceRecognizer
from brain.voice.commands import parse
from brain.voice import responder

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

_current_mode = 'active'
_mqtt: MQTTClient = None

def _on_mode_change(topic, payload):
    global _current_mode
    _current_mode = payload.get('mode', 'active')
    logger.info(f"Mode changed to: {_current_mode}")

def _on_recognized(text: str):
    """Called from recognizer thread with recognized text."""
    global _current_mode, _mqtt

    if text == '__wake__':
        logger.info("Wake word detected")
        responder.respond("Yes?")
        return

    logger.info(f"Recognized: '{text}'")

    if _current_mode == 'idle':
        logger.debug("In idle mode — suppressing command")
        return

    command_id, confidence = parse(text)
    if command_id is None:
        responder.unknown()
        return

    payload = {
        "command": command_id,
        "raw_phrase": text,
        "confidence": round(confidence, 3),
        "timestamp": time.time(),
    }
    logger.info(f"Publishing command: {command_id} (confidence={confidence:.2f})")
    if _mqtt:
        _mqtt.publish(TOPIC_VOICE_COMMANDS, payload)
    responder.confirm()

async def heartbeat_loop(mqtt: MQTTClient):
    while True:
        mqtt.publish(TOPIC_SYSTEM_HEARTBEAT, {"node": NODE_BRAIN + "/voice", "timestamp": time.time()})
        await asyncio.sleep(30)

async def main():
    global _mqtt

    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'brain.yaml')
    config = load_config(os.path.abspath(config_path))

    mqtt_cfg = config.get('mqtt', {})
    broker_host = mqtt_cfg.get('broker_host', '192.168.10.1')
    broker_port = mqtt_cfg.get('broker_port', 1883)

    voice_cfg = config.get('voice', {})
    model_path = voice_cfg.get('vosk_model_path', 'brain/voice/models/vosk-model-small-en-us')
    wake_word = voice_cfg.get('wake_word', 'cortana')
    sample_rate = voice_cfg.get('sample_rate', 16000)
    chunk_size = voice_cfg.get('chunk_size', 4000)
    command_timeout_s = voice_cfg.get('command_timeout_s', 3.0)
    confidence_threshold = voice_cfg.get('confidence_threshold', 0.80)
    device_index = voice_cfg.get('mic_device_index', None)

    _mqtt = MQTTClient(broker_host, broker_port, 'vh-voice')
    _mqtt.connect()
    _mqtt.subscribe(TOPIC_SYSTEM_MODE, _on_mode_change)

    recognizer = VoiceRecognizer(
        model_path=model_path,
        wake_word=wake_word,
        sample_rate=sample_rate,
        chunk_size=chunk_size,
        command_timeout_s=command_timeout_s,
    )
    recognizer.start(on_command=_on_recognized, device_index=device_index)
    logger.info(f"Voice service started — wake word: '{wake_word}'")

    try:
        await heartbeat_loop(_mqtt)
    except asyncio.CancelledError:
        pass
    finally:
        recognizer.stop()
        _mqtt.disconnect()
        logger.info("Voice service stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
