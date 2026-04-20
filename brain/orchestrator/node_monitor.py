import time
import logging

logger = logging.getLogger(__name__)

class NodeMonitor:
    def __init__(self):
        self._last_seen = {}  # node_name -> float timestamp

    def record_heartbeat(self, node_name: str, timestamp: float):
        self._last_seen[node_name] = time.time()  # use local time for consistency

    def get_status(self, node_name: str, threshold_s: float = 120.0) -> str:
        ts = self._last_seen.get(node_name)
        if ts is None:
            return "offline"
        age = time.time() - ts
        if age >= threshold_s:
            return "offline"
        if age >= threshold_s / 2:
            return "stale"
        return "online"

    def check_all(self, threshold_s: float = 120.0) -> dict:
        nodes = ['led', 'sensor', 'power']
        return {n: self.get_status(n, threshold_s) for n in nodes}
