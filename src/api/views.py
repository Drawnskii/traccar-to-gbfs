import time

from .constants import *

from src.odoo.jsonrpc_client import OdooClient, StationService

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from google.protobuf.json_format import MessageToDict

from src.translators.free_bike_status import FreeBikeStatus

app = FastAPI(title="Traccar to GBFS")

@app.get('/')
async def root():
    return {"message": "Traccar to GBFS is running!"}

@app.get("/gbfs.json")
async def gbfs_discovery():
    return JSONResponse(content={
        "last_updated": int(time.time()),
        "ttl": 30,
        "version": "2.2",
        "data": {
            LANGUAGE: {
                "feeds": FEEDS
            }
        }
    })

@app.get("/gbfs/system-information")
async def system_information():
    return JSONResponse(content={
        "last_updated": int(time.time()),
        "ttl": 30,
        "version": "2.2",
        "data": {
            "system_id": SYSTEM_ID,
            "language": LANGUAGE,
            "name": SYSTEM_NAME,
            "timezone": TIMEZONE,
            "url": SYSTEM_URL,
            "license_url": LICENSE_URL,
            "rental_apps": {
                "android":{
                    "discovery_uri":"com.abcrental.android://",
                    "store_uri": "https://play.google.com/store/apps/details?id=com.abcrental.android",
                },
                "ios":{
                    "discovery_uri":"com.abcrental.ios://",
                    "store_uri": "https://apps.apple.com/app/apple-store/id123456789",
                }
            }
        }
    })

# Create single instances (cache effect)
client = OdooClient()
station_service = StationService(client)

@app.get("/gbfs/station-information")
async def station_information():
    data = station_service.get_station_information()

    return JSONResponse(content={
        "last_updated": int(time.time()),
        "ttl": 0,
        "version": "2.2",
        "data": {
            "stations": data
        }
    })

@app.get("/gbfs/station-status")
async def station_status():
    data = station_service.get_station_status()

    return JSONResponse(content={
        "last_updated": int(time.time()),
        "ttl": 0,
        "version": "2.2",
        "data": {
            "stations": data
        }
    })

@app.get("/gbfs/vehicle-types")
def get_vehicle_types():
    current_timestamp = int(time.time())
    data = {
        "last_updated": current_timestamp,
        "ttl": 0,
        "version": "2.2",
        "data": {
            "vehicle_types": [
                {
                    "vehicle_type_id": "1",
                    "form_factor": "bicycle",
                    "propulsion_type": "human",
                    "name": "Ambato byke"
                },
                {
                    "vehicle_type_id": "2",
                    "form_factor": "scooter",
                    "propulsion_type": "electric",
                    "name": "Abato Scooter",
                    "max_range_meters": 12345
                },
                {
                    "vehicle_type_id": "3",
                    "form_factor": "car",
                    "propulsion_type": "combustion",
                    "name": "Four-door Sedan",
                    "max_range_meters": 523992
                }
            ]
        }
    }
    return JSONResponse(content=data)

@app.get("/gbfs/free-bike-status")
async def get_free_bike_status():
    feed = FreeBikeStatus.make()
    return feed