import logging
from time import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.context import context
from .trip_mapper import TripMapper
from src.factories.feed_message import FeedMessage
from src.factories.trip_update import TripUpdate

logger = logging.getLogger(__name__)

class TripUpdates:
    _known_ids = set()
    _last_feed = None
    _last_feed_time = datetime.min
    # Cache the feed for 10 seconds
    _cache_lifetime = timedelta(seconds=10)

    @staticmethod
    def make():
        now = datetime.now()
        
        # Return cached feed if it's still fresh
        if TripUpdates._last_feed and TripUpdates._last_feed_time + TripUpdates._cache_lifetime > now:
            logger.info("Using cached trip updates feed")
            return TripUpdates._last_feed
            
        start_time = time()
        updated = 0
        created = 0

        # Pre-allocate list
        estimated_size = len(context.data)
        trip_updates: List[Any] = []
        trip_updates.reserve(estimated_size) if hasattr(list, 'reserve') else None

        for data in context.data.values():
            if "position" not in data or "route_id" not in data:
                continue
                
            entity_id = data["id"]
            position = data["position"]
            route_id = data["route_id"]
            device_time = position["deviceTime"]

            # Get trip information
            trip_data = TripMapper.map(route_id, device_time)
            if trip_data is None:
                continue

            trip_id, stops = trip_data

            speed_kmh = position.get("speed", 25) * 3.6  # m/s a km/h

            params = {
                "entity_id": entity_id,
                "trip_id": trip_id,
                "stops": stops,
                "vehicle_id": data["name"],
                "latitude": position["latitude"],
                "longitude": position["longitude"],
                "speed_kmh": speed_kmh,
            }

            if entity_id in TripUpdates._known_ids:
                updated += 1
            else:
                created += 1
                TripUpdates._known_ids.add(entity_id)

            trip_update = TripUpdate.create(**params)
            trip_updates.append(trip_update)

        # Create feed
        feed = FeedMessage.create(entities=trip_updates)
        
        # Cache the feed
        TripUpdates._last_feed = feed
        TripUpdates._last_feed_time = now
        
        end_time = time()
        logger.info(f"TripUpdates feed created in {(end_time - start_time):.3f}s, Total: {len(trip_updates)}, New: {created}, Updated: {updated}")
        
        return feed
