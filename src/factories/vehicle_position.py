from datetime import datetime
from google.transit import gtfs_realtime_pb2 as gtfsrt

class VehiclePosition:
    @staticmethod
    def create(*args, **kwargs):
        entity_id = str(kwargs.get("entity_id"))

        # TripDescriptor: identifies the trip associated with this vehicle
        route_id = str(kwargs.get("route_id"))
        trip_id = str(kwargs.get("trip_id"))

        trip_descriptor = gtfsrt.TripDescriptor(
            route_id=route_id,
            trip_id=trip_id,
        )

        # VehicleDescriptor: uniquely identifies the vehicle
        vehicle_id = kwargs.get("vehicle_id")
        vehicle_descriptor = gtfsrt.VehicleDescriptor(id=vehicle_id)

        # Position: represents the current position and bearing of the vehicle
        latitude = kwargs.get("latitude")
        longitude = kwargs.get("longitude")
        bearing = kwargs.get("bearing")

        position = gtfsrt.Position(
            longitude=longitude,
            latitude=latitude, 
            bearing=bearing
        )

        current_stop_sequence = kwargs.get("current_stop_sequence")
        stop_id = str(kwargs.get("stop_id"))

        # VehiclePosition: encapsulates the real-time vehicle data
        vehicle_position = gtfsrt.VehiclePosition(
            position=position,
            trip=trip_descriptor,
            vehicle=vehicle_descriptor,
            current_stop_sequence=current_stop_sequence,
            current_status=gtfsrt.VehiclePosition.VehicleStopStatus.STOPPED_AT,
            stop_id=stop_id,
            timestamp=int(datetime.now().timestamp())
        )

        return gtfsrt.FeedEntity(
            id=entity_id,
            vehicle=vehicle_position
        )
