# Constants (can be pulled from config or database later)
LANGUAGE = "es"
SYSTEM_ID = "1"
SYSTEM_NAME = "Ambato"
TIMEZONE = "America/Guayaquil"
SYSTEM_URL = "https://www.ejemplo.ec"
LICENSE_URL = "https://www.ejemplo.ec/license"

# Feed URLs (these should match the actual routes)
BASE_URL = "http://localhost:8000/gbfs"
FEEDS = [
    {"name": "system_information", "url": f"{BASE_URL}/system-information"},
    {"name": "station_information", "url": f"{BASE_URL}/station-information"},
    {"name": "station_status", "url": f"{BASE_URL}/station-status"},
]