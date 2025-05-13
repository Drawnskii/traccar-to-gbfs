import asyncio
import logging

from .api.views import app
from uvicorn import Config, Server
from .websocket.traccar_client import WsTraccarClient

logger = logging.getLogger(__name__)

logging.basicConfig(
    encoding="utf-8",
    datefmt="%H:%M:%S",
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

async def main() -> None:
    wsc = WsTraccarClient()
    
    config = Config(app, host="0.0.0.0", port=8000)
    server = Server(config)

    wsc_task = asyncio.create_task(wsc.get_messages())
    api_task = asyncio.create_task(server.serve())

    await asyncio.gather(wsc_task, api_task)