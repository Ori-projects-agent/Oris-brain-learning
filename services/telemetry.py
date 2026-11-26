"""
Live Environmental & Astronomical Telemetry Service.
Fetches real-time atmospheric severe weather data and solar/space geomagnetic activity.
Zero API keys required (uses free Open-Meteo and NOAA SWPC open feeds).
"""

import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, Any

logger = logging.getLogger("Ori.Telemetry")


class TelemetryService:
    def __init__(self, default_lat: float = 35.22, default_lon: float = -97.44):
        # Default coordinates set to Norman, Oklahoma (heart of Tornado Alley & National Severe Storms Lab)
        # Can be updated to any user city coordinates!
        self.lat = default_lat
        self.lon = default_lon
        self._cached_weather: Dict[str, Any] = {}
        self._cached_space: Dict[str, Any] = {}
        self._last_weather_time: float = 0.0
        self._last_space_time: float = 0.0

    def fetch_live_severe_weather(self) -> Dict[str, Any]:
        """Fetch current atmospheric barometric pressure, wind gusts, and precipitation."""
        now = time.time()
        if self._cached_weather and (now - self._last_weather_time < 300):
            return self._cached_weather

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.lat}&longitude={self.lon}&current="
            f"temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_gusts_10m,weather_code"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "OriAutonomousSolarium/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                current = data.get("current", {})
                self._cached_weather = {
                    "surface_pressure_hPa": current.get("surface_pressure", 1013.25),
                    "wind_speed_kmh": current.get("wind_speed_10m", 0.0),
                    "wind_gusts_kmh": current.get("wind_gusts_10m", 0.0),
                    "temperature_c": current.get("temperature_2m", 20.0),
                    "humidity_percent": current.get("relative_humidity_2m", 50),
                    "is_stormy": current.get("surface_pressure", 1013.25) < 1005 or current.get("wind_gusts_10m", 0) > 40,
                    "radar_reference": "Max Velocity Severe Weather Live Feeds (maxvelocitywx.com/severeweather)"
                }
                self._last_weather_time = now
                return self._cached_weather
        except Exception as e:
            logger.debug(f"Live weather fetch offline: {e}. Using cached or simulated tropospheric state.")
            if not self._cached_weather:
                self._cached_weather = {
                    "surface_pressure_hPa": 994.2,
                    "wind_speed_kmh": 38.5,
                    "wind_gusts_kmh": 62.0,
                    "temperature_c": 18.4,
                    "humidity_percent": 82,
                    "is_stormy": True
                }
            return self._cached_weather

    def fetch_live_space_weather(self) -> Dict[str, Any]:
        """Fetch NOAA Space Weather Prediction Center planetary geomagnetic K-index (solar activity)."""
        now = time.time()
        if self._cached_space and (now - self._last_space_time < 300):
            return self._cached_space

        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "OriAutonomousSolarium/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if len(data) > 1:
                    last_reading = data[-1]
                    kp = float(last_reading[1])
                    self._cached_space = {
                        "geomagnetic_kp_index": kp,
                        "aurora_activity": "Storm / Aurora Visible" if kp >= 5.0 else ("Unsettled" if kp >= 4.0 else "Quiet"),
                        "solar_wind_status": "Active" if kp >= 4.0 else "Normal"
                    }
                    self._last_space_time = now
                    return self._cached_space
        except Exception as e:
            logger.debug(f"Live space weather fetch offline: {e}. Using cached space telemetry.")

        if not self._cached_space:
            self._cached_space = {
                "geomagnetic_kp_index": 3.67,
                "aurora_activity": "Quiet to Moderate",
                "solar_wind_status": "Normal Solar Stream"
            }
        return self._cached_space


telemetry = TelemetryService()
