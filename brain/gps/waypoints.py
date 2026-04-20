import json
import math
import threading
import os
import logging

logger = logging.getLogger(__name__)


class WaypointStore:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._waypoints = []
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    self._waypoints = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load waypoints: {e}")
                self._waypoints = []

    def _save(self):
        tmp = self.filepath + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(self._waypoints, f, indent=2)
        os.replace(tmp, self.filepath)

    def add(self, name: str, lat: float, lon: float):
        with self._lock:
            self._waypoints.append({"name": name, "lat": lat, "lon": lon})
            self._save()

    def remove(self, name: str):
        with self._lock:
            self._waypoints = [w for w in self._waypoints if w['name'] != name]
            self._save()

    def list_all(self) -> list:
        with self._lock:
            return list(self._waypoints)

    def nearest(self, lat: float, lon: float) -> dict | None:
        with self._lock:
            if not self._waypoints:
                return None
            best = None
            best_dist = float('inf')
            for wp in self._waypoints:
                dist = self._haversine(lat, lon, wp['lat'], wp['lon'])
                if dist < best_dist:
                    best_dist = dist
                    best = wp
            bearing = self._bearing(lat, lon, best['lat'], best['lon'])
            return {**best, "distance_m": round(best_dist, 1), "bearing_deg": round(bearing, 1)}

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _bearing(self, lat1, lon1, lat2, lon2) -> float:
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.atan2(x, y)
        return (math.degrees(bearing) + 360) % 360
