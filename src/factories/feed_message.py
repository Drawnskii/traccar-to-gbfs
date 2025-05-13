import time

from google.transit import gtfs_realtime_pb2 as gtfsrt

class FeedMessage:
    VERSION = "2.0"

    @staticmethod
    def create(*args, **kwargs):
        entities = kwargs.get("entities", {})

        header = gtfsrt.FeedHeader(
            gtfs_realtime_version=FeedMessage.VERSION,
            incrementality=gtfsrt.FeedHeader.FULL_DATASET,
            timestamp = int(time.time())
        )

        message = gtfsrt.FeedMessage(header=header, entity=entities)

        return message

