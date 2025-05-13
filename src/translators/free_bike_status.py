import logging
from time import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from src.context import context

logger = logging.getLogger(__name__)

class FreeBikeStatus:
    """
    Generates the free_bike_status data dictionary according to GBFS v2.2 specification.
    Uses data from the shared context and includes caching.
    """
    _last_feed: Optional[Dict[str, Any]] = None
    _last_feed_time: datetime = datetime.min.replace(tzinfo=timezone.utc) # Use timezone-aware datetime
    _cache_lifetime: timedelta = timedelta(seconds=10) # Cache duration

    @staticmethod
    def make() -> Dict[str, Any]:
        """
        Creates the free_bike_status feed dictionary.

        Returns:
            A dictionary representing the free_bike_status.json structure.
        """
        now = datetime.now(timezone.utc)

        # Return cached feed if it's still fresh
        if FreeBikeStatus._last_feed and FreeBikeStatus._last_feed_time + FreeBikeStatus._cache_lifetime > now:
            logger.info("Using cached free bike status feed")
            # Return a copy to prevent modification of the cache
            # Update the last_updated timestamp to reflect access time,
            # although the data itself is from the cache time.
            # Alternatively, we could return the exact cached object including its original timestamp.
            # Let's return the cached object directly for consistency with vehicle_positions cache logic.
            return FreeBikeStatus._last_feed

        start_time = time()
        
        bikes_data: List[Dict[str, Any]] = []

        # Process data from context
        for item_id, data in context.data.items():
            # Filter for bikes that are likely available and have position data
            if data.get("status") != "online" or data.get("disabled") is True:
                continue
                
            position = data.get("position")
            if not position or "latitude" not in position or "longitude" not in position:
                 logger.debug(f"Skipping bike ID {item_id} due to missing position data.")
                 continue

            last_update_str = data.get("lastUpdate")
            if not last_update_str:
                logger.warning(f"Skipping bike ID {item_id} due to missing lastUpdate.")
                continue
                
            # Convert lastUpdate string (ISO format) to Unix timestamp
            try:
                # Ensure timezone info is handled correctly ('Z' or +HH:MM)
                last_update_dt = datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
                # Ensure it's offset-aware before timestamping if it wasn't already
                if last_update_dt.tzinfo is None:
                   last_update_dt = last_update_dt.replace(tzinfo=timezone.utc) # Assume UTC if no offset
                last_reported_ts = int(last_update_dt.timestamp())
            except ValueError:
                logger.warning(f"Skipping bike ID {item_id} due to invalid lastUpdate format: {last_update_str}")
                continue

            # Map data to GBFS free_bike_status fields
            try:
                 bike_entry = {
                    # NOTE: GBFS requires rotating bike_id after each trip for privacy.
                    # Using uniqueId directly might not comply fully if it's persistent.
                    "bike_id": data["uniqueId"],
                    "lat": float(position["latitude"]), # Ensure float type
                    "lon": float(position["longitude"]), # Ensure float type
                    "is_reserved": False, # Assumption: No reservation info available in source data
                    "is_disabled": data["disabled"],
                    # Assumption: All vehicles processed here are type 'bicycle'
                    # based on the target feed name and user provided types.
                    "vehicle_type_id": "1",
                    "last_reported": last_reported_ts,
                }
                 # Add optional fields if available and applicable
                 # Example: current_range_meters if vehicle_type supported it and data was available
                 # Example: station_id if vehicle was docked and data was available
                 
                 bikes_data.append(bike_entry)
            except KeyError as e:
                 logger.warning(f"Skipping bike ID {item_id} due to missing key: {e}")
                 continue
            except (ValueError, TypeError) as e:
                 logger.warning(f"Skipping bike ID {item_id} due to data type error (e.g., for position): {e}")
                 continue

        # Create the final GBFS structure
        current_timestamp = int(now.timestamp())
        feed = {
            "last_updated": current_timestamp,
            "ttl": 0, # Time To Live: 0 indicates data should be refreshed frequently
            "version": "2.2", # GBFS version
            "data": {
                "bikes": bikes_data
            }
        }

        # Cache the generated feed
        FreeBikeStatus._last_feed = feed
        FreeBikeStatus._last_feed_time = now # Store the time when this data was generated

        end_time = time()
        logger.info(f"FreeBikeStatus feed created in {(end_time - start_time):.3f}s, Found: {len(bikes_data)} available bikes")

        return feed
