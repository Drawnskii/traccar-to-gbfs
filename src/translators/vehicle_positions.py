import logging
from time import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.context import context
from .trip_mapper import TripMapper
from src.factories.feed_message import FeedMessage
from src.factories.vehicle_position import VehiclePosition

logger = logging.getLogger(__name__)

class VehiclePositions:
    _known_ids = set()
    _last_feed = None
    _last_feed_time = datetime.min
    # Cache the feed for 10 seconds
    _cache_lifetime = timedelta(seconds=10)

    @staticmethod
    def make():
        now = datetime.now()
        
        # Return cached feed if it's still fresh
        if VehiclePositions._last_feed and VehiclePositions._last_feed_time + VehiclePositions._cache_lifetime > now:
            logger.info("Using cached vehicle positions feed")
            return VehiclePositions._last_feed
        
        start_time = time()
        updated = 0
        created = 0

        # Pre-allocate the list with an estimated size
        estimated_size = len(context.data)
        vehicle_positions: List[Any] = []
        vehicle_positions.reserve(estimated_size) if hasattr(list, 'reserve') else None
        
        # Batch process the positions
        for data in context.data.values():
            if "position" not in data:
                continue
                
            entity_id = data["id"]
            position = data.get("position", {})
            
            if "route_id" not in data:
                continue
                
            route_id = data["route_id"]
            device_time = position["deviceTime"]

            # Get trip information
            trip_data = TripMapper.map(route_id, device_time)
            if trip_data is None:
                continue

            trip_id, stops = trip_data

            # Create vehicle position entity
            params = {
                "entity_id": entity_id,
                "route_id": route_id,
                "trip_id": trip_id,
                "stop_id": stops[0]["stop_id"],
                "vehicle_id": data["name"],
                "bearing": position["course"],
                "latitude": position["latitude"],
                "longitude": position["longitude"],
                "current_stop_sequence": stops[0]["stop_sequence"]
            }

            # Track known IDs
            if entity_id in VehiclePositions._known_ids:
                updated += 1
            else:
                created += 1
                VehiclePositions._known_ids.add(entity_id)

            vehicle_position = VehiclePosition.create(**params)
            vehicle_positions.append(vehicle_position)
        
        # Create feed message
        feed = FeedMessage.create(entities=vehicle_positions)
        
        # Cache the feed
        VehiclePositions._last_feed = feed
        VehiclePositions._last_feed_time = now
        
        end_time = time()
        logger.info(f"VehiclePositions feed created in {(end_time - start_time):.3f}s, Total: {len(vehicle_positions)}, New: {created}, Updated: {updated}")

        return feed

