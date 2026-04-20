import sys
import os
import json
import asyncio
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.mqtt_client import MQTTClient
from shared.constants import (
    TOPIC_VOICE_COMMANDS,
    TOPIC_AUDIO_STATUS,
    TOPIC_SYSTEM_MODE,
    TOPIC_SYSTEM_HEARTBEAT,
    NODE_BRAIN,
    MODE_POWER_SAVE,
)
from shared.config_loader import load_config
from brain.audio.bluetooth import BluetoothManager
from brain.audio.volume import VolumeController
from brain.audio.mixer import AudioMixer

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

_mixer: AudioMixer = None


def speak(text: str):
    if _mixer is not None:
        _mixer.speak(text)
    else:
        logger.warning("speak() called before audio service initialised")


def _build_status(bt: BluetoothManager, vol: VolumeController) -> dict:
    return {
        "connected": bt.is_connected(),
        "device_name": bt.get_device_name() if bt.is_connected() else None,
        "volume": vol.get_volume(),
        "timestamp": time.time(),
    }


async def _heartbeat_loop(mqtt: MQTTClient, bt: BluetoothManager, vol: VolumeController):
    while True:
        try:
            mqtt.publish(TOPIC_SYSTEM_HEARTBEAT, {
                "node": NODE_BRAIN,
                "service": "audio",
                "timestamp": time.time(),
            })
            mqtt.publish(TOPIC_AUDIO_STATUS, _build_status(bt, vol))
        except Exception as e:
            logger.warning(f"Heartbeat publish failed: {e}")
        await asyncio.sleep(30)


def main():
    global _mixer

    config_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'config', 'brain.yaml'
    )
    config = load_config(os.path.normpath(config_path))

    audio_cfg = config.get('audio', {})
    mqtt_cfg = config.get('mqtt', {})

    bt_mac = audio_cfg.get('bluetooth_device_mac', '')
    volume_default_pct = audio_cfg.get('volume_music_pct', 70)
    volume_power_save_pct = audio_cfg.get('volume_power_save_pct', 40)
    tts_duck_pct = audio_cfg.get('tts_duck_music_pct', 20)

    # Piper model path: prefer audio section, fall back to voice section
    piper_model_path = audio_cfg.get(
        'piper_model_path',
        config.get('voice', {}).get('tts_model', '')
    )

    mqtt = MQTTClient(
        broker_host=mqtt_cfg.get('broker_host', 'localhost'),
        broker_port=mqtt_cfg.get('broker_port', 1883),
        client_id=f"{NODE_BRAIN}-audio",
    )
    mqtt.connect()

    vol = VolumeController()
    vol.set_volume(volume_default_pct)

    def on_bt_status(connected: bool, device_name):
        mqtt.publish(TOPIC_AUDIO_STATUS, {
            "connected": connected,
            "device_name": device_name,
            "volume": vol.get_volume(),
            "timestamp": time.time(),
        })

    bt = BluetoothManager(mac_address=bt_mac, on_status_change=on_bt_status)
    _mixer = AudioMixer(
        volume_controller=vol,
        tts_duck_pct=tts_duck_pct,
        piper_model_path=piper_model_path,
    )

    bt.start_auto_reconnect()

    def handle_voice_commands(topic, payload):
        command = payload.get('command', '')
        if command == 'music_play':
            bt.send_media_command('Play')
        elif command == 'music_pause':
            bt.send_media_command('Pause')
        elif command == 'music_next':
            bt.send_media_command('Next')
        elif command == 'music_prev':
            bt.send_media_command('Previous')
        elif command == 'volume_up':
            vol.set_volume(vol.get_volume() + 10)
        elif command == 'volume_down':
            vol.set_volume(vol.get_volume() - 10)
        else:
            logger.debug(f"Unhandled voice command: {command}")

    def handle_system_mode(topic, payload):
        mode = payload.get('mode', '')
        if mode == MODE_POWER_SAVE:
            logger.info("Power save mode — reducing volume")
            vol.set_volume(volume_power_save_pct)

    mqtt.subscribe(TOPIC_VOICE_COMMANDS, handle_voice_commands)
    mqtt.subscribe(TOPIC_SYSTEM_MODE, handle_system_mode)

    logger.info("Audio service started")

    async def run():
        await _heartbeat_loop(mqtt, bt, vol)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Audio service shutting down")
        bt.stop_auto_reconnect()
        bt.disconnect()
        mqtt.disconnect()


if __name__ == '__main__':
    main()
