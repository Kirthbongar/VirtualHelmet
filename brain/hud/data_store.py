import threading
import time
import logging

logger = logging.getLogger(__name__)

class DataStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}       # topic -> payload dict
        self._timestamps = {} # topic -> float (time.time() when last updated)

    def update(self, topic: str, payload: dict):
        with self._lock:
            self._data[topic] = payload
            self._timestamps[topic] = time.time()

    def get(self, topic: str) -> dict | None:
        with self._lock:
            return self._data.get(topic)

    def is_stale(self, topic: str, warn_threshold_s: float = 60.0, offline_threshold_s: float = 120.0) -> str:
        with self._lock:
            ts = self._timestamps.get(topic)
        if ts is None:
            return "offline"
        age = time.time() - ts
        if age >= offline_threshold_s:
            return "offline"
        if age >= warn_threshold_s:
            return "stale"
        return "fresh"
