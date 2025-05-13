import time
import requests

from pathlib import Path
from dotenv import dotenv_values
from typing import List, Dict
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor


class OdooConfig:
    def __init__(self):
        dotenv_path = Path(__file__).parent / ".env"
        config = dotenv_values(dotenv_path)

        self.url = config["URL"]
        self.db = config["DB"]
        self.username = config["USERNAME"]
        self.password = config["PASSWORD"]


class OdooClient:
    def __init__(self, config: OdooConfig = None):
        self.config = config or OdooConfig()
        self.uid = self.authenticate()

    def authenticate(self) -> int:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "login",
                "args": [self.config.db, self.config.username, self.config.password],
            },
            "id": 1,
        }
        response = requests.post(self.config.url, json=payload).json()
        uid = response.get("result")
        if not uid:
            raise Exception("Authentication failed. Please check your credentials.")
        return uid

    def execute_kw(self, model: str, method: str, args: list, kwargs: dict = None):
        if kwargs is None:
            kwargs = {}
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [self.config.db, self.uid, self.config.password, model, method, args, kwargs],
            },
            "id": 2,
        }
        response = requests.post(self.config.url, json=payload).json()
        return response.get("result")


class StationService:
    def __init__(self, client: OdooClient):
        self.client = client

    @lru_cache(maxsize=1)
    def get_all_station_ids(self) -> List[int]:
        return self.client.execute_kw("bike_municipal.station", "search", [[]]) or []

    @lru_cache(maxsize=1)
    def get_station_information(self) -> List[Dict]:
        station_ids = self.get_all_station_ids()
        if not station_ids:
            return []

        stations = self.client.execute_kw(
            "bike_municipal.station",
            "read",
            [station_ids],
            {"fields": ["id", "name", "latitude", "longitude", "station_line_ids"]},
        )

        return [
            {
                "station_id": str(station["id"]),
                "name": station.get("name", "Unnamed Station"),
                "lat": float(station.get("latitude", 0.0)),
                "lon": float(station.get("longitude", 0.0)),
                "capacity": len(station["station_line_ids"]),
                "is_virtual_station": False,
                "rental_uris": {
                    "android": f"https://example.com/app?sid={station['id']}&platform=android",
                    "ios": f"https://example.com/app?sid={station['id']}&platform=ios",
                    "web": f"https://example.com/app?sid={station['id']}",
                },
            }
            for station in stations
        ]

    def _get_station_status(self, station: Dict) -> Dict:
        station_lines = self.client.execute_kw(
            "bike_municipal.station.line",
            "read",
            [station["station_line_ids"]],
            {"fields": ["is_free"]},
        )

        num_bikes_available = sum(1 for line in station_lines if line.get("is_free"))
        num_bikes_disabled = len(station_lines) - num_bikes_available
        total_docks = len(station["station_line_ids"])

        return {
            "station_id": str(station["id"]),
            "num_bikes_available": num_bikes_available,
            "num_bikes_disabled": num_bikes_disabled,
            "num_docks_available": total_docks - num_bikes_available,
            "num_docks_disabled": 0,
            "is_installed": True,
            "is_renting": True,
            "is_returning": True,
            "last_reported": int(time.time()),
        }

    def get_station_status(self) -> List[Dict]:
        station_ids = self.get_all_station_ids()
        if not station_ids:
            return []

        stations = self.client.execute_kw(
            "bike_municipal.station",
            "read",
            [station_ids],
            {"fields": ["id", "station_line_ids"]},
        )

        # Parallel processing of stations
        with ThreadPoolExecutor() as executor:
            status_list = list(executor.map(self._get_station_status, stations))

        return status_list
