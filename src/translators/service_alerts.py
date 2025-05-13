import logging
from datetime import datetime, timedelta

from src.context import context
from .trip_mapper import TripMapper
from src.factories.feed_message import FeedMessage
from src.factories.service_alert import ServiceAlert

logger = logging.getLogger(__name__)

class ServiceAlerts:
    _known_ids = set()

    @staticmethod
    def make():
        updated = 0
        created = 0

        service_alerts = []

        for data in context.data.values():
            if "position" in data:
                route_id = data["route_id"]
                event = data.get("event", {})

                event_type = event.get("type")
                attributes = event.get("attributes", {})
                alarm = attributes.get("alarm", "")

                is_valid_event = (
                    event_type == "geofenceExited" or
                    (event_type == "alarm" and alarm == "geofenceExited")
                )

                if not is_valid_event:
                    continue

                event_time = event["eventTime"].replace("Z", "+00:00")

                vehicle_name = data["name"]

                params = {
                    "entity_id": f"D{event['id']}",
                    "route_id": route_id,
                    "event_time": event_time,
                    "effect": "DETOUR",
                    "language": "es",
                    "header_text": "Alerta de Desvío",
                    "description_text": f"Vehículo {vehicle_name}, salió de la geocerca con la ruta {route_id}"
                }

                service_alert = ServiceAlert.create(**params)
                service_alerts.append(service_alert)

        logger.info(f"ServiceAlerts feed created. Total: {len(service_alerts)}, New: {created}, Updated: {updated}")
        
        return FeedMessage.create(entities=service_alerts)
