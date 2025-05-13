import os
import pytz
import pandas as pd
import logging
from functools import lru_cache
from typing import Dict, List, Tuple, Optional

from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.context import gtfs_context

load_dotenv()

logger = logging.getLogger(__name__)

class TripMapper:
    # Cache for storing previously calculated trip mappings
    _cache: Dict[str, Tuple[str, List[Dict]]] = {}
    # Cache expiration time (in seconds)
    _cache_expiry: Dict[str, datetime] = {}
    # Cache lifetime (10 minutes)
    _cache_lifetime = timedelta(minutes=10)

    @staticmethod
    def map(route_id, device_time):
        dt = datetime.fromisoformat(device_time.replace("Z", "+00:00"))
        
        timezone = pytz.timezone(os.getenv("timezone"))
        dt = dt.astimezone(timezone)

        date = dt.strftime("%Y%m%d")
        time = dt.strftime("%H:%M:%S")
        
        # Create a cache key based on route_id and approximate time (rounded to the nearest minute)
        rounded_time = dt.replace(second=0, microsecond=0)
        cache_key = f"{route_id}_{date}_{rounded_time.strftime('%H:%M')}"
        
        # Check if we have a valid cached result
        now = datetime.now()
        if cache_key in TripMapper._cache and TripMapper._cache_expiry.get(cache_key, datetime.min) > now:
            return TripMapper._cache[cache_key]
            
        # If not in cache or expired, calculate the mapping
        result = TripMapper._calculate_mapping(route_id, dt, date, time)
        
        # Cache the result if valid
        if result:
            TripMapper._cache[cache_key] = result
            TripMapper._cache_expiry[cache_key] = now + TripMapper._cache_lifetime
            
            # Clean old cache entries
            expired_keys = [k for k, v in TripMapper._cache_expiry.items() if v <= now]
            for k in expired_keys:
                TripMapper._cache.pop(k, None)
                TripMapper._cache_expiry.pop(k, None)
        
        return result
    
    @staticmethod
    def _calculate_mapping(route_id, dt, date, time) -> Optional[Tuple[str, List[Dict]]]:
        weekday = dt.strftime("%A").lower()

        calendar = gtfs_context.calendar
        calendar = calendar[(calendar[weekday] == 1)]
        calendar = calendar[(calendar["start_date"] <= int(date)) & (calendar["end_date"] >= int(date))]

        active_services = calendar["service_id"].unique()

        trips = gtfs_context.trips
        today_trips = trips[(trips["route_id"] == int(route_id)) & trips["service_id"].isin(active_services)]

        merged = pd.merge(today_trips, gtfs_context.stop_times, on='trip_id')
        first_stops = merged.sort_values(["trip_id", "stop_sequence"]).groupby("trip_id").first().reset_index()

        if first_stops.empty:
            return None

        first_stops["time_diff"] = first_stops["departure_time"].apply(
            lambda t: abs((datetime.strptime(t, "%H:%M:%S") - datetime.strptime(time, "%H:%M:%S")).total_seconds())
        )

        best_match = first_stops.sort_values("time_diff").iloc[0]
        trip_id = best_match["trip_id"]

        # Get all stops for this trip
        trip_stops = merged[merged["trip_id"] == trip_id].sort_values("stop_sequence")

        stops_df = pd.merge(trip_stops, gtfs_context.stops, on="stop_id")

        stops = []
        
        for _, row in stops_df.iterrows():
            stops.append({
                "stop_sequence": int(row["stop_sequence"]),
                "stop_id": row["stop_id"],
                "stop_lat": row["stop_lat"],
                "stop_lon": row["stop_lon"],
                "arrival_time": row["arrival_time"]
            })

        return trip_id, stops
