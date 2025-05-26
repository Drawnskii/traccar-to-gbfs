import json
import logging
import pandas as pd

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

    def load_data(self, message):
        if "positions" in message:
            for position in message["positions"]:
                device_id = position["deviceId"]
                self.data[device_id] = position
        
        # Write to file less frequently, e.g., only for debugging
        with open("data.json", "w") as f:
            json.dump(self.data, f, indent=4)

context: DataContext = DataContext()