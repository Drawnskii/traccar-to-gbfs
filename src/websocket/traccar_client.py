import orjson
import logging
import requests

from .config import config
from src.context import context

from typing import Dict, Any
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

class TraccarSession:
    def __init__(self) -> None:
        self._url = config["URL"]
        self._email = config["EMAIL"]
        self._password = config["PASSWORD"]
        self._cookie: str = self._login().split(';')[0]

    def _login(self) -> str:
        response = requests.post(
            f"{self._url}/session?email={self._email}&password={self._password}",
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
            }
        )

        if response.status_code != 200 and "Set-Cookie" not in response.headers:
            logger.error("Attempt to log in failed. Be sure that the provided credentials are correct.")
            return None

        logger.info("Logging successful.")
        return response.headers["Set-Cookie"]

class WsTraccarClient(TraccarSession):
    def __init__(self) -> None:
        super().__init__()
        self._uri = f"{self._url.replace('http', 'ws')}/socket?wstoken=access"
        self._headers = {"Cookie": self._cookie}

    async def get_messages(self) -> None:
        try:
            async for websocket in connect(self._uri, additional_headers=self._headers):
                try:
                    while True:
                        message: Dict[str, Any] = orjson.loads(await websocket.recv())

                        logger.info("Message recived!")
                        
                        context.load_data(message)
                except ConnectionClosed:
                    logger.info("Connection to Traccar WebSocket closed. Attempting to reconnect...")
                    continue
        except Exception as e:
            logger.critical(f"Conecction to web socket failed: {e}")