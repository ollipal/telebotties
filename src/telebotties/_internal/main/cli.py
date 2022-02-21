import asyncio

from ..log_formatter import get_logger, setup_logging
from ..string_utils import error_to_string
from ..websocket import Client
from .telebotties_base import TelebottiesBase

logger = get_logger()


class Cli(TelebottiesBase):
    def __init__(self):
        self.client = None
        super().__init__()

    def post_done(self, future):
        if future.result() is False:  # Send failed
            logger.info("Keyboard disconnected")
            if self.keyboard_listener.running:
                self.keyboard_listener.stop()

    def event_handler(self, event):
        event._update(True, -1)
        future = asyncio.run_coroutine_threadsafe(
            self.client.send(event), self.loop
        )
        self.register_future(future)

    async def main(self):
        try:
            self.client = Client(8080)
            try:
                await self.client.connect(connect_as="player")
            except ConnectionRefusedError:
                print(
                    "Connection refused to 127.0.0.1:8080, "
                    "wrong address or bot not running?"
                )
                return

            await self.keyboard_listener.run_until_finished()
            await self.client.stop()
        except Exception as e:
            logger.error(f"Unexpected internal error: {error_to_string(e)}")
            if self.keyboard_listener.running:
                self.keyboard_listener.stop()
            if self.client is not None:
                await self.client.stop()

    def sigint_callback(self):
        pass


def _cli():
    setup_logging("DEBUG")
    Cli().run()
