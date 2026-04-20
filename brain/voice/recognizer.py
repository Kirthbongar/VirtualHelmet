import json
import logging
import threading
import time
import queue

import pyaudio
import vosk

logger = logging.getLogger(__name__)

class VoiceRecognizer:
    def __init__(self, model_path: str, wake_word: str, sample_rate: int = 16000,
                 chunk_size: int = 4000, command_timeout_s: float = 3.0):
        self.wake_word = wake_word.lower()
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.command_timeout_s = command_timeout_s

        logger.info(f"Loading Vosk model from {model_path}")
        self.model = vosk.Model(model_path)
        self._recognizer = vosk.KaldiRecognizer(self.model, sample_rate)

        self._audio = pyaudio.PyAudio()
        self._stream = None
        self._running = False
        self._audio_queue = queue.Queue()
        self._callback = None  # callable(text: str)

    def _audio_callback(self, in_data, frame_count, time_info, status):
        self._audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start(self, on_command, device_index=None):
        """Start listening. on_command(text: str) called with recognized command text."""
        self._callback = on_command
        self._running = True

        kwargs = dict(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback,
        )
        if device_index is not None:
            kwargs['input_device_index'] = device_index

        self._stream = self._audio.open(**kwargs)
        self._stream.start_stream()

        thread = threading.Thread(target=self._recognition_loop, daemon=True)
        thread.start()

    def _recognition_loop(self):
        in_command_mode = False
        command_start = 0.0
        command_audio = []

        while self._running:
            try:
                data = self._audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if not in_command_mode:
                # Ambient listening — look for wake word in partial results
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get('text', '').lower()
                    if self.is_wake_word(text):
                        in_command_mode = True
                        command_start = time.time()
                        command_audio = []
                        self._recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
                        if self._callback:
                            self._callback('__wake__')
                else:
                    partial = json.loads(self._recognizer.PartialResult())
                    text = partial.get('partial', '').lower()
                    if self.is_wake_word(text):
                        in_command_mode = True
                        command_start = time.time()
                        command_audio = []
                        self._recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
                        if self._callback:
                            self._callback('__wake__')
            else:
                # Command mode — buffer audio until timeout
                command_audio.append(data)
                elapsed = time.time() - command_start

                self._recognizer.AcceptWaveform(data)

                if elapsed >= self.command_timeout_s:
                    result = json.loads(self._recognizer.FinalResult())
                    text = result.get('text', '').lower()
                    # Strip wake word from command text
                    text = text.replace(self.wake_word, '').strip()
                    if text and self._callback:
                        self._callback(text)
                    in_command_mode = False
                    self._recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

    def is_wake_word(self, text: str) -> bool:
        return self.wake_word in text.lower()

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        self._audio.terminate()
