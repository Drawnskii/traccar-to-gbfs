import pytz
from geopy.distance import geodesic
from datetime import datetime, timedelta
from google.transit import gtfs_realtime_pb2 as gtfsrt

class TripUpdate:
    @staticmethod
    def create(*, entity_id, trip_id, vehicle_id, latitude, longitude, stops, speed_kmh=30):
        now = datetime.now(pytz.timezone("America/Guayaquil"))
        current_pos = (float(latitude), float(longitude))

        trip_descriptor = gtfsrt.TripDescriptor(trip_id=str(trip_id))
        vehicle_descriptor = gtfsrt.VehicleDescriptor(id=str(vehicle_id))
        stop_time_updates = []

        for stop in stops:
            try:
                stop_sequence = int(stop["stop_sequence"])
                stop_lat = float(stop["stop_lat"])
                stop_lon = float(stop["stop_lon"])
                arrival_time_str = stop["arrival_time"]

                scheduled_arrival = datetime.strptime(arrival_time_str, "%H:%M:%S").replace(
                    year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo
                )

                stop_pos = (stop_lat, stop_lon)
                distance_km = geodesic(current_pos, stop_pos).km
                eta_seconds = (distance_km / speed_kmh) * 3600 if speed_kmh > 0 else 0
                estimated_arrival = now + timedelta(seconds=eta_seconds)
                delay = int((estimated_arrival - scheduled_arrival).total_seconds())

                stop_time_update = gtfsrt.TripUpdate.StopTimeUpdate(
                    stop_sequence=stop_sequence
                )
                stop_time_update.arrival.delay = delay
                stop_time_updates.append(stop_time_update)

            except Exception as e:
                raise ValueError(f"Error processing stop {stop}: {e}")

        trip_update = gtfsrt.TripUpdate(
            trip=trip_descriptor,
            vehicle=vehicle_descriptor,
            stop_time_update=stop_time_updates,
            timestamp=int(now.timestamp())
        )

        return gtfsrt.FeedEntity(
            id=str(entity_id),
            trip_update=trip_update
        )
