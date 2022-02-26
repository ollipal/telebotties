from ..constants import INPUT_EVENT, SYSTEM_EVENT
from ..log_formatter import get_logger, setup_logging
from ..string_utils import error_to_string
from ..websocket import Client
from .telebotties_base import TelebottiesBase

logger = get_logger()


class Cli(TelebottiesBase):
    def __init__(self):
        super().__init__()
        self.client = None
        self.callback_executor.add_to_takes_event(self._forward_event)

    async def _forward_event(self, event):
        send_success = await self.client.send(event)

        if not send_success or event._type == SYSTEM_EVENT:
            return False

    def event_handler(self, event):
        if event._type == INPUT_EVENT:
            event._update(True, -1)
        self.callback_executor.execute_callbacks(
            [self._forward_event], event=event
        )

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
            self.keyboard_listener.stop()
            if self.client is not None:
                await self.client.stop()

    def done_callback(self, future):
        if future.result() is False:  # Send failed or Esc pressed
            logger.info("Keyboard disconnected")
            self.keyboard_listener.stop()

    def sigint_callback(self):
        pass


def _cli():
    setup_logging("DEBUG")
    Cli().run()
