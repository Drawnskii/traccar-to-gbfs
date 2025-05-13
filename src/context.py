import re
import json
import logging
import pandas as pd

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent  # Va al root del proyecto
GTFS_PATH = BASE_DIR / "gtfs"

class SingletonMeta(type):
    _instaces = {}

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if cls not in cls._instaces:
            instace = super().__call__(*args, **kwds)
            cls._instaces[cls] = instace

        return cls._instaces[cls]
    

class DataContext(metaclass=SingletonMeta):
    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}
        self.routes_ids = {
            1: "55",
            2: "50",
            3: "62",
            4: "53",
            5: "54",
            6: "60",
            7: "51",
            8: "52",
            9: "56",
            10: "57",
            11: "58",
            12: "59",
            59: "61",
            60: "64",
            61: "63",
        }

    def load_data(self, positions, devices, events):
        if "devices" in devices:
            for device in devices["devices"]:
                self.data[device["id"]] = device

        if "events" in events:
            for event in events:
                device_id = event["deviceId"]
                if device_id in self.data:
                    self.data[device_id]["event"] = event

        if "positions" in positions:
            for position in positions["positions"]:
                device_id = position["deviceId"]
                if device_id in self.data: 
                    self.data[device_id]["position"] = position

        # self.test_events()
        
        # Write to file less frequently, e.g., only for debugging
        # with open("data.json", "w") as f:
        #     json.dump(self.data, f, indent=4)

    def test_events(self) -> None:
        alternate = True

        for data in self.data.values():
            device_id = data["id"]

            now = datetime.now()

            base_event = {
                "id": device_id,
                "deviceId": device_id,
                "eventTime": now.strftime("%Y-%m-%dT%H:%M:%S.000+00:00"),
                "positionId": data.get("positionId", 0),
                "geofenceId": 0,
                "maintenanceId": 0,
                "busStopId": 0
            }

            if alternate:
                event = {
                    **base_event,
                    "type": "alarm",
                    "attributes": {
                        "alarm": "geofenceExited"
                    }
                }
            else:
                event = {
                    **base_event,
                    "type": "geofenceExited",
                    "attributes": {}
                }

            data["event"] = event
            
            alternate = not alternate


class GtfsDataContext(metaclass=SingletonMeta):
    def __init__(self):
        # Load GTFS data with optimized dtype specifications for memory efficiency
        self.trips = pd.read_csv(
            GTFS_PATH / "trips.txt",
            dtype={
                'route_id': 'int32',
                'service_id': 'category',
                'trip_id': 'str',
                'trip_headsign': 'category',
                'direction_id': 'int8',
                'shape_id': 'category'
            }
        )
        
        self.stops = pd.read_csv(
            GTFS_PATH / "stops.txt",
            dtype={
                'stop_id': 'str',
                'stop_name': 'category',
                'stop_lat': 'float32',
                'stop_lon': 'float32'
            }
        )
        
        self.calendar = pd.read_csv(
            GTFS_PATH / "calendar.txt",
            dtype={
                'service_id': 'category',
                'monday': 'int8',
                'tuesday': 'int8',
                'wednesday': 'int8',
                'thursday': 'int8',
                'friday': 'int8',
                'saturday': 'int8',
                'sunday': 'int8',
                'start_date': 'int32',
                'end_date': 'int32'
            }
        )
        
        self.stop_times = pd.read_csv(
            GTFS_PATH / "stop_times.txt",
            dtype={
                'trip_id': 'str',
                'arrival_time': 'str',
                'departure_time': 'str',
                'stop_id': 'str',
                'stop_sequence': 'int16'
            }
        )
        
        # Pre-process stop_times to optimize frequently used queries
        self._prepare_stop_times_index()
        
        logger.info("GTFS data loaded successfully")
        
    def _prepare_stop_times_index(self):
        # Create an index on trip_id for faster lookup
        self.stop_times.set_index('trip_id', inplace=True)
        self.stop_times.sort_index(inplace=True)
        
        # We'll reset it when needed in specific queries

context: DataContext = DataContext()
gtfs_context: GtfsDataContext = GtfsDataContext()